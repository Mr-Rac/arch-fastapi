class AuthError:
    INVALID_TOKEN = "Could not validate credentials"
    INVALID_USER = "Could not found user"
    INVALID_SCOPES = "Could not validate scope"
    EXPIRED_SCOPES = "Expired scopes"


class UserError:
    NOT_FOUND = "user not found"
    INCORRECT_PASSWORD = "Incorrect password."


class RoleError:
    NOT_FOUND = "role not found"


class PermError:
    NOT_FOUND = "permission not found"
