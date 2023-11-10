from flask_login import  current_user
from flask import  abort


def admin_only(func_to_protect):
    """
    Check if current is admin and is authenticated
    :param func_to_protect: func
    :return: 403 error if unsuccessful or successful  func_to_protect(*args, **kwargs)
    """

    def check_admin_status(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_admin == 1:

            return func_to_protect(*args, **kwargs)
        else:
            # If not, don't run the function and show a 403 error instead.
            return abort(403)

    return check_admin_status