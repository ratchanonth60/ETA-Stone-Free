from functools import wraps


def login_required_graphql(func):
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        if not info.context.user.is_authenticated:
            raise Exception("You must be logged in to perform this action")
        return func(self, info, *args, **kwargs)

    return wrapper
