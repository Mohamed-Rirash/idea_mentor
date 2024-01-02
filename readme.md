# database moduls


## users
 - id
 - email
 - firstname
 - lastname
 - username
 - password
 - is_active



###### Note: it has relation ship to projects


## Projects
- id
- project title
- project profile image 
- breife description
- detailed description
- created date
- status = compleated,progress or pending
###### Note: it has relation ship to todos

## Todos
- id
- task title
- task description 
- status = compleated or not = bool
###### Note: it has relation ship to resorces


## resource
- id
- resour title
- resource description 
- link = compleated or not = bool
- type = pdf ,article multimedai_ resource