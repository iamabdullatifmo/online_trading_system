from flask import Flask, render_template,session,url_for,flash

app = Flask(__name__)

@app.route("/Create_account")
def create_account():
    return render_template()

if __name__ == '__main__':
    app.run(debug=True)