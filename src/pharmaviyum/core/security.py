from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from src.pharmaviyum.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenData(BaseModel):
	username: str | None = None


async def get_current_user(token: str = Depends(oauth2_scheme)):
	if not token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
	try:
		payload = jwt.decode(token, settings.API_SECRET_KEY or "", algorithms=["HS256"])  # type: ignore[arg-type]
		username: str = payload.get("sub")
		if username is None:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
		token_data = TokenData(username=username)
	except JWTError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
	return token_data

