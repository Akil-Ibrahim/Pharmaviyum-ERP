
from fastapi import HTTPException, status


def require_role(user: object, role: str):
	# user is expected to be token data or object with roles attribute
	roles = getattr(user, "roles", None)
	if roles is None:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
	if role not in roles:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
