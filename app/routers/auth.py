from fastapi import APIRouter,status,HTTPException,Depends,Request
from app.database_dependency import db_dependency
import app.schemas as schemas
import app.models as models
from passlib.context import CryptContext
from datetime import timedelta, datetime
from jose import jwt,JWTError
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
# google sign in 
from authlib.integrations.starlette_client import OAuth
# otp 
from email.message import EmailMessage
import ssl
import smtplib
import pyotp
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone
# from app.config import CLIENT_ID,CLIENT_SECRET,SECRET_KEY,ALGORITHM,EMAIL_PASSWORD,EMAIL_SENDER,OTP_SECRET_KEY



router = APIRouter(
    prefix="/auth",
    tags=["auth"]
  
)

oauth = OAuth()
oauth.register(
    name='google',
    client_id= CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'}
)

secret_key = SECRET_KEY
algorithm = ALGORITHM


bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')



# step 1: authenticate user
def authenticate_user(db, password: str, username: str = None):
    user = None
    if username and '@' in username:
        user = db.query(models.User).filter(models.User.email == username).first()
    elif username:
        user = db.query(models.User).filter(models.User.username == username).first()
    else:
        return False

    if user and bcrypt_context.verify(password, user.hashed_password):
        return user
    return False



# step 2: create access token
def create_access_token(username: str, user_id: int,expires_delta = timedelta):
    encode ={'sub': username, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, secret_key,algorithm=algorithm)



# step 3: get current user
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token,secret_key,algorithms=[algorithm])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="could not validate user")
        return {"username": username, "id": user_id, }
    except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="could not validate user")


user_dependency = Annotated[dict, Depends(get_current_user)]

'''-------------------------------------------------otp start---with sign up----------------------------------------------------------'''


email_sender = EMAIL_SENDER
email_password = EMAIL_PASSWORD
otp_secret_key = OTP_SECRET_KEY



def otp_generator():
    totp = pyotp.TOTP(otp_secret_key)
    print(otp_secret_key)
    return totp.now()

async def send_verification_email(receiver_email, otp):
    subject = f'{otp} is your ideamentor code'
    body = f"""
    ideamentor is your ideamentor code

        Log in to ideamentor
        Welcome back! Enter this code within the next 10 minutes to log in:

                        {otp}
    """
    em = EmailMessage()
    em["from"] = email_sender
    em["to"] = receiver_email
    em['subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, receiver_email, em.as_string())
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/new_user", status_code=status.HTTP_201_CREATED, summary="Create new user account / sign up")
async def create_new_user(userrequest: schemas.UserRequest, db: db_dependency, otp: int = Depends(otp_generator)):
    
    '''  ## Sign Up

    This endpoint is used for creating a new user account with the following fields:

    - **email**: "user@example.com" (_unique_)
    - **firstname**: "string"
    - **lastname**: "string"
    - **username**: "string" (_unique_)
    - **password**: "string" (_password with validation in fields_)
    - **is_active**: true (_it is by default true; no need for manipulation_)
    '''

    try:
        create_user_model = models.User(
            firstname=userrequest.firstname,
            lastname=userrequest.lastname,
            email=userrequest.email,
            username=userrequest.username,
            hashed_password=bcrypt_context.hash(userrequest.hashed_password),
            is_active=userrequest.is_active
        )
        db.add(create_user_model)
        db.commit()

        await send_verification_email(create_user_model.email, otp)

        # Store the OTP and email in your database with an expiration time
        otp_record = models.OTPRecord(email=userrequest.email, otp=otp)
        db.add(otp_record)
        db.commit()

        return {"message": "Email sent successfully with OTP!"}
    except Exception as e:
        # Rollback changes if any exception occurs during user creation or email sending
        db.rollback()
        # You can log the exception for debugging purposes
        print(f"An error occurred: {str(e)}")
        # Raise an HTTPException with a 500 Internal Server Error status code and an error message
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user and send email")

@router.post("/resend_otp", status_code=status.HTTP_200_OK, summary="Resend OTP to user's email")
async def resend_otp(email: str, db: db_dependency):

    """
    ## resend otp code
    this endpoint is for resending the otp code and  cancels the previous one so the second code will be walid
    > it has email parameter"""


    # Verify if user email exists in the database
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cancel the previous OTP by deleting or invalidating it
    previous_otp_record = db.query(models.OTPRecord).filter(models.OTPRecord.email == email).first()
    if previous_otp_record:
        db.delete(previous_otp_record)
        db.commit()

    # Generate a new OTP
    new_otp = otp_generator()

    # Send the new OTP via email
    try:
        await send_verification_email(email, new_otp)

        # Store the new OTP in the database
        new_otp_record = models.OTPRecord(email=email, otp=new_otp)
        db.add(new_otp_record)
        db.commit()

        return {"message": "New OTP sent successfully!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resend OTP: {str(e)}")

@router.post("/verify/{code}", summary="Verify that the email used to sign up is yours")
async def enter_the_code(code: int, db: db_dependency):
    """
    ## Verification page
    
    > Allow the user a place to enter 6 integer digits

    ** Note: ** otp code is valid around 10 minitues
    """
    otp_validity_duration = timedelta(minutes=10)

    # Retrieve the stored OTP and timestamp from the database using the code
    otp_record = db.query(models.OTPRecord).filter(models.OTPRecord.otp == str(code)).first()

    if not otp_record:
        raise HTTPException(status_code=404, detail="OTP record not found or already used")

    # Make current_time timezone-aware (assuming UTC)
    current_time = datetime.now(timezone.utc)
    otp_creation_time = otp_record.created_at
    otp_expiry_time = otp_creation_time + otp_validity_duration

    if current_time > otp_expiry_time:
        raise HTTPException(status_code=410, detail="OTP has expired")

    # Use the email from the OTP record to find the corresponding user
    user = db.query(models.User).filter(models.User.email == otp_record.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.is_active = True
        db.delete(otp_record)  # Delete OTP record after successful verification
        db.commit()
        return {"message": "Verification successful and user activated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




'''-----------------------------------------------------------------------------------------------------------------'''


# login 

@router.post("/token", response_model=schemas.Token, summary="Login endpoint")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    '''
    ## Login
    #### It can verify both:
    - Username
    - Email
    ** with password **
    '''
    try:
        user = None
        if form_data.username:
            user = authenticate_user(username=form_data.username, password=form_data.password, db=db)
        elif form_data.email:
            user = authenticate_user(email=form_data.email, password=form_data.password, db=db)

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        # Log the exception for debugging purposes
        # print(f"An error occurred during login: {str(e)}")
        # Raise a more general HTTP 500 server error for unhandled exceptions
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during login")

# google oauth




@router.get('/login/google', summary="Redirects to Google for login")
async def login_via_google(request: Request):
    try:
        redirect_uri = request.url_for('auth_via_google')
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        print(f"Error during Google login redirect: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error redirecting to Google for login")

@router.get('/auth/google', summary="Google OAuth callback endpoint")
async def auth_via_google(request: Request, db: db_dependency):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)

        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')

        user = get_or_create_user_from_google_data(email, first_name, last_name, db)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User creation failed")

        access_token = create_access_token(username=user.username, user_id=user.id)  # Use your existing token creation logic
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during Google authentication: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error during Google authentication")



def generate_username(email, first_name, last_name):
    # Simple example: use part of the email or first and last name
    # You can make this more sophisticated to ensure uniqueness
    username_base = email.split('@')[0]
    return f"{username_base}_{first_name.lower()}"


def get_or_create_user_from_google_data(email, first_name, last_name, db):
    # Check if user already exists based on email
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        # User doesn't exist, create a new one
        # Generate a username from the email or other data
        username = generate_username(email, first_name, last_name)

        # For Google OAuth, there might not be a password, so consider how to handle it
        # Here, we are setting it to None, but ensure your authentication logic can handle it
        hashed_password = None

        user = models.User(
            email=email,
            firstname=first_name,
            lastname=last_name,
            username=username,
            hashed_password=hashed_password,
            is_active=True  # Assuming the user should be active upon creation
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user if needed
        user.firstname = first_name
        user.lastname = last_name
        # Update other fields as necessary
        db.commit()

    return user

