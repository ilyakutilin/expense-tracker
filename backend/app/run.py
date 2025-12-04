"""
Custom uvicorn runner to disable default logging
"""

import uvicorn

from app.core.settings import settings

if __name__ == "__main__":
    log_level = settings.log_settings.STREAM_LEVEL.lower()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Disable uvicorn's default logging config
        log_level=log_level,
    )
