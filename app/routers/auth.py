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
# import os
from app.config import CLIENT_ID,CLIENT_SECRET,SECRET_KEY,ALGORITHM,EMAIL_PASSWORD,EMAIL_SENDER,OTP_SECRET_KEY



router = APIRouter(
    prefix="/auth",
    tags=["auth"]
  
)



secret_key = SECRET_KEY
algorithm =  ALGORITHM


bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')



# step 1: authenticate user
def authenticate_user(username_or_email: str, password: str, db: db_dependency):
    # Check if the input is an email or username based on the presence of '@'
    if '@' in username_or_email:
        user = db.query(models.User).filter(models.User.email == username_or_email).first()
    else:
        user = db.query(models.User).filter(models.User.username == username_or_email).first()

    
    if user and bcrypt_context.verify(password, user.hashed_password):
        return user
    return None




# step 2: create access token
def create_access_token(username: str, user_id: int):
    access_token_expires = timedelta(minutes=15) 
    refresh_token_expires = timedelta(days=7)  

    access_token = jwt.encode(
        {"sub": username, "id": user_id, "exp": datetime.utcnow() + access_token_expires},
        SECRET_KEY, algorithm=ALGORITHM)

    refresh_token = jwt.encode(
        {"sub": username, "id": user_id, "exp": datetime.utcnow() + refresh_token_expires},
        SECRET_KEY, algorithm=ALGORITHM)

    return access_token, refresh_token




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
otp_secret_key =  OTP_SECRET_KEY


def otp_generator():
    totp = pyotp.TOTP(otp_secret_key)
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

    This endpoint is used for creating a new user account.
    '''

    # Check if the user already exists based on email or username
    existing_user = db.query(models.User).filter((models.User.email == userrequest.email) | (models.User.username == userrequest.username)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered with the given email or username")
    
    try:
        create_user_model = models.User(
            firstname=userrequest.firstname,
            lastname=userrequest.lastname,
            email=userrequest.email,
            username=userrequest.username,
            hashed_password=bcrypt_context.hash(userrequest.password),
            is_active=False
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
        db.rollback()  # Rollback changes if any exception occurs
        # For debugging purposes, you might want to log the exception here
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
# Assuming authenticate_user expects parameters like (username_or_email, password, db)
@router.post("/token", response_model=schemas.TokenResponse, summary="Login endpoint")
async def login_for_access_token( db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()
                                ):
    '''
    ## Login
    #### It can verify both:
    - Username
    - Email
    ** with password **
    '''

    # Since OAuth2PasswordRequestForm does not directly provide a 'username' field,
    # we assume 'username' is used here to mean either an actual username or email.
    # So, the form_data.username will contain either the username or the email.
    user = authenticate_user(username_or_email=form_data.username, password=form_data.password, db=db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please activate your account")

    access_token, refresh_token = create_access_token(username=user.username, user_id=user.id)

    return schemas.TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", summary="Refresh access token")
async def refresh_token(refresh_token: str, db: db_dependency):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        new_access_token, new_refresh_token = create_access_token(username, user_id)
        return schemas.TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token or expired token")







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

