from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI

#from .dependencies import get_query_token, get_token_header
#from .internal import admin
from routers import ( messages, services, timers )

app = FastAPI(dependencies=[])#Depends(get_query_token)])

origins = [
    'http://localhost:27017', # To set up with MongoDB.
    'http://localhost:3000'   # To set up with React front-end.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

@app.get("/")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    # Filter out docs and this function from the results
    url_list = [x for x in url_list if ( 'doc' not in x['path'] and 'api' not in x['path'] and x['path'] != '/')]
    return url_list

# Attach each of the routers to the main application.
app.include_router(messages.router)
app.include_router(services.router)
app.include_router(timers.router)