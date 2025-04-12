from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
import google.generativeai as genai  # Import genai
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not GENAI_API_KEY:
    raise ValueError("GENAI_API_KEY not found in environment variables.")

genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


@app.route('/')
def login():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    if 'user_id' in session:  # if logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("login.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    if 'user_id' not in session:  # if user not logged-in
        email = request.form.get('email')
        passwd = request.form.get('password')
        query = """SELECT * FROM user_login WHERE email LIKE '{}' AND password LIKE '{}'""".format(email, passwd)
        users = support.execute_query("search", query)
        if len(users) > 0:  # if user details matched in db
            session['user_id'] = users[0][0]
            return redirect('/home')
        else:  # if user details not matched in db
            flash("Invalid email and password!")
            return redirect('/')
    else:  # if user already logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')


@app.route('/reset', methods=['POST'])
def reset():
    if 'user_id' not in session:
        email = request.form.get('femail')
        pswd = request.form.get('pswd')
        userdata = support.execute_query('search', """select * from user_login where email LIKE '{}'""".format(email))
        if len(userdata) > 0:
            try:
                query = """update user_login set password = '{}' where email = '{}'""".format(pswd, email)
                support.execute_query('insert', query)
                flash("Password has been changed!!")
                return redirect('/')
            except:
                flash("Something went wrong!!")
                return redirect('/')
        else:
            flash("Invalid email address!!")
            return redirect('/')
    else:
        return redirect('/home')


@app.route('/register')
def register():
    if 'user_id' in session:  # if user is logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("register.html")


@app.route('/registration', methods=['POST'])
def registration():
    if 'user_id' not in session:  # if not logged-in
        name = request.form.get('name')
        email = request.form.get('email')
        passwd = request.form.get('password')
        # Removed length check
        # if len(name) > 5 and len(email) > 10 and len(passwd) > 5:  # if input details satisfy length condition
        try:
            query = """INSERT INTO user_login(username, email, password) VALUES('{}','{}','{}')""".format(name,
                                                                                                          email,
                                                                                                          passwd)
            support.execute_query('insert', query)

            user = support.execute_query('search',
                                         """SELECT * from user_login where email LIKE '{}'""".format(email))
            session['user_id'] = user[0][0]  # set session on successful registration
            flash("Successfully Registered!!")
            return redirect('/home')
        except:
            flash("Email id already exists, use another email!!")
            return redirect('/register')
        # else:  # if input condition length not satisfy
        #     flash("Not enough data to register, try again!!")
        #     return redirect('/register')
    else:  # if already logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    sub = request.form.get("sub")
    message = request.form.get("message")
    flash("Thanks for reaching out to us. We will contact you soon.")
    return redirect('/')


@app.route('/home')
def home():
    if 'user_id' in session:  # if user is logged-in
        query = """select * from user_login where user_id = {} """.format(session['user_id'])
        userdata = support.execute_query("search", query)

        table_query = """select * from user_expense where user_id = {} order by pdate desc""".format(
            session['user_id'])
        table_data = support.execute_query("search", table_query)
        df = pd.DataFrame(table_data, columns=['#', 'User_Id', 'Date', 'Expense', 'Amount', 'Note'])

        df = support.generate_df(df)
        try:
            earning, spend, invest, saving = support.top_tiles(df)
        except:
            earning, spend, invest, saving = 0, 0, 0, 0

        try:
            bar, pie, line, stack_bar = support.generate_Graph(df)
        except:
            bar, pie, line, stack_bar = None, None, None, None
        try:
            monthly_data = support.get_monthly_data(df, res=None)
        except:
            monthly_data = []
        try:
            card_data = support.sort_summary(df)
        except:
            card_data = []

        try:
            goals = support.expense_goal(df)
        except:
            goals = []
        try:
            size = 240
            pie1 = support.makePieChart(df, 'Earning', 'Month_name', size=size)
            pie2 = support.makePieChart(df, 'Spend', 'Day_name', size=size)
            pie3 = support.makePieChart(df, 'Investment', 'Year', size=size)
            pie4 = support.makePieChart(df, 'Saving', 'Note', size=size)
            pie5 = support.makePieChart(df, 'Saving', 'Day_name', size=size)
            pie6 = support.makePieChart(df, 'Investment', 'Note', size=size)
        except:
            pie1, pie2, pie3, pie4, pie5, pie6 = None, None, None, None, None, None
        return render_template('home.html',
                               user_name=userdata[0][1],
                               df_size=df.shape[0],
                               df=jsonify(df.to_json()),
                               earning=earning,
                               spend=spend,
                               invest=invest,
                               saving=saving,
                               monthly_data=monthly_data,
                               card_data=card_data,
                               goals=goals,
                               table_data=table_data[:4],
                               bar=bar,
                               line=line,
                               stack_bar=stack_bar,
                               pie1=pie1,
                               pie2=pie2,
                               pie3=pie3,
                               pie4=pie4,
                               pie5=pie5,
                               pie6=pie6,
                               )
    else:  # if not logged-in
        return redirect('/')


@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            date = request.form.get('e_date')
            amount = request.form.get('amount')
            comment = request.form.get('comment')

            # Basic logic to categorize the expense based on keywords in the comment
            expense_type = categorize_expense(comment) # Define this function as described below.

            try:
                query = """insert into user_expense (user_id, pdate, expense, amount, pdescription) values 
                ({}, '{}','{}',{},'{}')""".format(user_id, date, expense_type, amount, comment)
                support.execute_query('insert', query)
                flash("Saved!!")
            except Exception as e:
                flash(f"Something went wrong: {e}")
                return redirect("/home")
            return redirect('/home')
    else:
        return redirect('/')

def categorize_expense(comment):
    """
    Categorizes an expense based on keywords in the comment.  You'll need to
    adapt this to your specific categories and keywords.
    """
    comment = comment.lower()
    if "salary" in comment or "bonus" in comment:
        return "Earning"
    elif "investment" in comment or "mutual fund" in comment:
        return "Investment"
    elif "saving" in comment or "bank" in comment:
        return "Saving"
    else:
        return "Spend" # Default to "Spend" if no keywords are found
@app.route('/analysis')
def analysis():
    if 'user_id' in session:  # if already logged-in
        query = """select * from user_login where user_id = {} """.format(session['user_id'])
        userdata = support.execute_query('search', query)
        query2 = """select pdate,expense, pdescription, amount from user_expense where user_id = {}""".format(
            session['user_id'])

        data = support.execute_query('search', query2)
        df = pd.DataFrame(data, columns=['Date', 'Expense', 'Note', 'Amount(₹)'])
        df = support.generate_df(df)

        if df.shape[0] > 0:
            pie = support.meraPie(df=df, names='Expense', values='Amount(₹)', hole=0.7, hole_text='Expense',
                                  hole_font=20,
                                  height=180, width=180, margin=dict(t=1, b=1, l=1, r=1))
            df2 = df.groupby(['Note', "Expense"]).sum().reset_index()[["Expense", 'Note', 'Amount(₹)']]
            bar = support.meraBarChart(df=df2, x='Note', y='Amount(₹)', color="Expense", height=180, x_label="Category",
                                       show_xtick=False)
            line = support.meraLine(df=df, x='Date', y='Amount(₹)', color='Expense', slider=False, show_legend=False,
                                    height=180)
            scatter = support.meraScatter(df, 'Date', 'Amount(₹)', 'Expense', 'Amount(₹)', slider=False, )
            heat = support.meraHeatmap(df, 'Day_name', 'Month_name', height=200, title="Transaction count Day vs Month")
            month_bar = support.month_bar(df, 280)
            sun = support.meraSunburst(df, 280)

            return render_template('analysis.html',
                                   user_name=userdata[0][1],
                                   pie=pie,
                                   bar=bar,
                                   line=line,
                                   scatter=scatter,
                                   heat=heat,
                                   month_bar=month_bar,
                                   sun=sun
                                   )
        else:
            flash("No data records to analyze.")
            return redirect('/home')

    else:  # if not logged-in
        return redirect('/')


@app.route('/profile')
def profile():
    if 'user_id' in session:  # if logged-in
        query = """select * from user_login where user_id = {} """.format(session['user_id'])
        userdata = support.execute_query('search', query)
        return render_template('profile.html', user_name=userdata[0][1], email=userdata[0][2])
    else:  # if not logged-in
        return redirect('/')


@app.route("/updateprofile", methods=['POST'])
def update_profile():
    name = request.form.get('name')
    email = request.form.get("email")
    query = """select * from user_login where user_id = {} """.format(session['user_id'])
    userdata = support.execute_query('search', query)
    query = """select * from user_login where email = "{}" """.format(email)
    email_list = support.execute_query('search', query)
    if name != userdata[0][1] and email != userdata[0][2] and len(email_list) == 0:
        query = """update user_login set username = '{}', email = '{}' where user_id = '{}'""".format(name, email,
                                                                                                      session[
                                                                                                          'user_id'])
        support.execute_query('insert', query)
        flash("Name and Email updated!!")
        return redirect('/profile')
    elif name != userdata[0][1] and email != userdata[0][2] and len(email_list) > 0:
        flash("Email already exists, try another!!")
        return redirect('/profile')
    elif name == userdata[0][1] and email != userdata[0][2] and len(email_list) == 0:
        query = """update user_login set email = '{}' where user_id = '{}'""".format(email, session['user_id'])
        support.execute_query('insert', query)
        flash("Email updated!!")
        return redirect('/profile')
    elif name == userdata[0][1] and email != userdata[0][2] and len(email_list) > 0:
        flash("Email already exists, try another!!")
        return redirect('/profile')

    elif name != userdata[0][1] and email == userdata[0][2]:
        query = """update user_login set username = '{}' where user_id = '{}'""".format(name, session['user_id'])
        support.execute_query('insert', query)
        flash("Name updated!!")
        return redirect("/profile")
    else:
        flash("No Change!!")
        return redirect("/profile")


@app.route('/logout')
def logout():
    try:
        session.pop("user_id")  # delete the user_id in session (deleting session)
        return redirect('/')
    except:  # if already logged-out but in another tab still logged-in
        return redirect('/')


@app.route('/chat')
def chat():
    """Renders the chat page."""
    if 'user_id' not in session:
        return redirect('/')  # Redirect to login if not logged in

    query = """select * from user_login where user_id = {} """.format(session['user_id'])
    userdata = support.execute_query("search", query)
    user_name = userdata[0][1]

    # Fetch expense data for the user
    expense_summary = support.get_expense_summary(session['user_id'])  # Implement this in support.py

    return render_template('chat.html', user_name=user_name, expense_summary=expense_summary)

@app.route('/ask', methods=['POST'])
def ask_gemini():
    """
    Endpoint to receive a text prompt and return Gemini's response.
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Missing "content" in request body'}), 400

        user_content = data['content']

        # Get user's expense summary
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        expense_summary = support.get_expense_summary(user_id)

        # Combine user's prompt with expense data for context
        context = f"You are a personal finance assistant. Answer questions based on the following expense data: {expense_summary}.  Now answer the user question: "
        prompt_with_context = context + user_content

        response = model.generate_content(prompt_with_context)
        return jsonify({'response': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai_assistance')
def ai_assistance():
    """Renders the AI Assistance page."""
    if 'user_id' not in session:
        return redirect('/')  # Redirect to login if not logged in

    query = """select * from user_login where user_id = {} """.format(session['user_id'])
    userdata = support.execute_query("search", query)
    user_name = userdata[0][1]

    return render_template('ai_assistance.html', user_name=user_name)

@app.route('/generate_ai_content', methods=['POST'])
def generate_ai_content():
    """
    Endpoint to generate AI content (insights or budgeting tips) using Gemini.
    """
    try:
        data = request.get_json()
        if not data or 'content_type' not in data:
            return jsonify({'error': 'Missing "content_type" in request body'}), 400

        content_type = data['content_type']

        # Get user's expense data
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        expense_summary = support.get_expense_summary(user_id)

        # Construct the prompt based on the content type
        if content_type == 'insights':
            prompt = f"You are a personal finance expert. Analyze this dataset: {expense_summary} that includes columns. Identify non-essential or excessive spending by category. Provide a short pointer one liner briefly explaining the unusual high spending, highlighting areas where the user might be overspending based on typical daily needs. Limit the points to only 5 and entire content to 40 words. Present each insight as a separate bullet point, using markdown format.(Also add some cool emojies). Don't provide heading"
        elif content_type == 'budgeting_tips':
            prompt = f"You are a financial advisor.Based on the categories and amounts in this expense dataset: {expense_summary}, provide 5 realistic, actionable suggestions to help the user reduce or optimize spending. Limit the entire content to 40 words by focussing on practical tips that can be implemented without drastically changing lifestyle, and prioritize savings on non-essential expenses. Present each insight as a separate bullet point, using markdown format. (Also add some cool emojies). Don't provide heading"
        else:
            return jsonify({'error': 'Invalid content_type'}), 400

        response = model.generate_content(prompt)
        # Split the response into lines and format as HTML list
        formatted_response = "<ul>"
        for line in response.text.splitlines():
            line = line.replace("*", "").strip()  # Remove leading asterisks and spaces
            if line:
                 formatted_response += f"<li>{line}</li>"
        formatted_response += "</ul>"

        return jsonify({'response': formatted_response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)
