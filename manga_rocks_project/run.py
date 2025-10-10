from manga_rocks import create_app, db

app = create_app()

if __name__ == "__main__":
    #craete tables if any models exist (safe at early stage)
    with app.app_context():
        db.create_all()
    #simple dev server
    app.run(debug=True, host="127.0.0.1", port=5000)