from smoservice.forum import views


# настраиваем пути, которые будут вести к нашей странице
def setup_routes(app):
    app.router.add_get("/tegroSuccess", views.index)
