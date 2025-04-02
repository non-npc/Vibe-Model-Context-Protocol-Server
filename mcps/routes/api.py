from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, List
from ..analyzer.code_analyzer import CodeAnalyzer
from ..auth.auth import get_current_user, create_access_token, authenticate_user
from datetime import timedelta
import os

router = APIRouter()
analyzer = None

@router.post("/token")
async def login_for_access_token(username: str, password: str):
    if not authenticate_user(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/analyze")
async def analyze_project(
    project_path: str,
    current_user: str = Depends(get_current_user)
) -> Dict:
    global analyzer
    if not os.path.exists(project_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project path not found"
        )
    
    analyzer = CodeAnalyzer(project_path)
    return analyzer.analyze_project()

@router.get("/context")
async def get_context(
    file_path: Optional[str] = None,
    current_user: str = Depends(get_current_user)
) -> Dict:
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No project is being analyzed"
        )
    
    return analyzer.get_context(file_path)

@router.get("/dependencies")
async def get_dependencies(
    current_user: str = Depends(get_current_user)
) -> List[str]:
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No project is being analyzed"
        )
    
    context = analyzer.get_context()
    return list(context.get('dependencies', []))

@router.get("/structure")
async def get_project_structure(
    current_user: str = Depends(get_current_user)
) -> Dict:
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No project is being analyzed"
        )
    
    context = analyzer.get_context()
    return context.get('structure', {}) 