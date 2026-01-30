# TODO: Remove Cognito and Implement Local Authentication

## Tasks
- [x] Update `app/api/v1/endpoints/signup.py` to use local authentication instead of Cognito
- [x] Remove oauth router from `app/api/v1/router.py`
- [x] Verify all endpoints use local JWT authentication
- [ ] Test all auth endpoints with Postman
- [ ] Ensure proper error handling and best practices

## Completed
- [x] Analyze current code and identify Cognito usage
- [x] Create plan for local authentication implementation
- [x] Get user approval for plan
- [x] Update `app/api/v1/endpoints/login.py` to use local authentication instead of Cognito
