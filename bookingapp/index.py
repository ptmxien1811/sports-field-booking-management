from flask import render_template
from bookingapp import app

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def products_list():
    return render_template("products.html")

if __name__ == "__main__":
    app.run(debug=True)