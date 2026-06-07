from fastapi import Request


def get_tenant_from_request(request: Request) -> str | None:
	# Simple tenancy extraction from header; override as needed
	return request.headers.get("X-Tenant-ID")
