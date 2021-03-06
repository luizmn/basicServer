from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash,
                   session,
                   g,
                   make_response)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Category, Base, Product, User, db_string
from flask import session as login_session
from functools import wraps
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests

app = Flask(__name__)
app.secret_key = 'super_secret_key'

csrf = CSRFProtect(app)

APP_PATH = '/var/www/html/carparts/'
CLIENT_ID = (json.loads(open(APP_PATH + 'client_secrets.json', 'r').read())
             ['web']['client_id'])

APPLICATION_NAME = "Car Parts Catalog"

# Connect to Database and create database session
db = create_engine(db_string)

Session = sessionmaker(db)
session = Session()



# Create anti-forgery state token
@csrf.exempt
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    categories = session.query(Category).order_by(asc(Category.name))
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state, categories=categories)


@csrf.exempt
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Facebook login."""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?' \
          'grant_type=fb_exchange_token&client_id=%s&client_secret=%s' \
          '&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we
        have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls.
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s' \
          '&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s' \
          '&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; '
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@csrf.exempt
@app.route('/fbdisconnect')
def fbdisconnect():
    """Disconnect facebook user."""
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = ('https://graph.facebook.com/%s/permissions?access_token=%s'
           % (facebook_id, access_token))
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google login."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = (make_response(json.dumps('User is already connected.'),
                                  200))
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += ' " -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    """Create new user in database."""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        print "user not found"
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@csrf.exempt
@app.route('/gdisconnect')
def gdisconnect():
    """Disconnect google user."""
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(
                   json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
                   json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Category Information
@app.route('/categories/<int:category_id>/JSON')
def categoryListJSON(category_id):
    """Returns JSON of one category."""
    categories = session.query(Category).filter_by(id=category_id).all()
    return jsonify(Categories=[i.serialize for i in categories])


@app.route('/products/<int:category_id>/<int:list_id>/JSON')
def listItemJSON(category_id, list_id):
    """Returns JSON of one product in one category."""
    categories = session.query(Category).filter_by(id=category_id).one()
    return jsonify(categories=categories.serialize)


@app.route('/categories/JSON')
def categoriesJSON():
    """Returns JSON of all categories."""
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/products/JSON')
def productsJSON():
    """Returns JSON of all products in catalog."""
    categories = session.query(Product).all()
    return jsonify(categories=[r.serialize for r in categories])


# Show all categories
@app.route('/')
@app.route('/category/')
def showCategories():
    """Returns all categories."""
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)

# Create a new Category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    """Create a new Category."""
    # The query below is used to populate the left menu
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(user_id=login_session['user_id'],
                               name=request.form['name'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html', categories=categories)


# Edit a Category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    """Edit a Category."""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        flash('You are not permitted to edit the {} category. '
              'Please create your own category to edit.'.format(category.name))
        return redirect(url_for('newCategory'))
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' %
                  editedCategory.name)
            return redirect(url_for('showCategories', categories=categories))
    else:
        return render_template('editcategory.html',
                               category=editedCategory, categories=categories)


# Delete a Category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Delete a specific Category and its products."""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        flash('You are not permitted do delete the {} category. Please create '
              'your own category.'.format(category.name))
        return redirect(url_for('showCategories'))
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategories',
                                category_id=category_id,
                                categories=categories))
    else:
        return render_template('deletecategory.html',
                               category=categoryToDelete,
                               categories=categories)


# Show products list
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/list/')
def showList(category_id):
    """List all products in one specific category."""
    categories = session.query(Category).order_by(asc(Category.name))
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except NoResultFound:
        category = '1'
    creator = getUserInfo(category.user_id)
    items = session.query(Product).filter_by(category_id=category_id).all()
    qtyproducts = len(items)
    if (
       'username' not in login_session
       or creator.id != login_session['user_id']
       ):
        return render_template('publiclist.html',
                               items=items,
                               category=category,
                               creator=creator,
                               categories=categories,
                               qtyproducts=qtyproducts)
    else:
        return render_template('list.html',
                               items=items,
                               category=category,
                               creator=creator,
                               categories=categories,
                               qtyproducts=qtyproducts)


# Create a new Product
@app.route('/category/<int:category_id>/list/new/', methods=['GET', 'POST'])
def newProduct(category_id):
    """Create a new product in one specific category."""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).first()
    if login_session['user_id'] != category.user_id:
        flash('You are not authorized to add products to {} category. Please '
              'create your own category do add items.'.format(category.name))
        return redirect(url_for('newCategory'))
    if request.method == 'POST':
        newProduct = Product(name=request.form['name'],
                             description=request.form['description'],
                             price=request.form['price'],
                             picture=request.form['picture'],
                             category_id=category_id,
                             user_id=category.user_id)
        session.add(newProduct)
        flash('%s Successfully Created' % newProduct.name)
        session.commit()
        return redirect(url_for('showList', category_id=category_id))
    else:
        return render_template('newproduct.html',
                               category=category,
                               categories=categories)


# Edit a product
@app.route('/category/<int:category_id>/list/<int:product_id>/edit',
           methods=['GET', 'POST'])
def editProduct(category_id, product_id):
    """Edit a product in one specific category."""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    editedItem = session.query(Product).filter_by(id=product_id).one()
    if login_session['user_id'] != category.user_id:
        flash('You are not permitted edit {}. '
              'Please create your own product to edit.'.format(editedItem.name))
        return redirect(url_for('newProduct', category_id=category_id))
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['picture']:
            editedItem.picture = request.form['picture']
        session.add(editedItem)
        session.commit()
        flash('Successfully Edited')
        return redirect(url_for('showList',
                                category_id=category_id,
                                categories=categories))
    else:
        return render_template('editproduct.html',
                               category_id=category_id,
                               product_id=product_id,
                               item=editedItem,
                               categories=categories)


# Show product page
@app.route('/category/<int:category_id>/list/<int:product_id>/show',
           methods=['GET', 'POST'])
def showProduct(category_id, product_id):
    """List product information in one specific category."""
    categories = session.query(Category).order_by(asc(Category.name))
    item = session.query(Product).filter_by(id=product_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return render_template('publicinfo.html',
                               category=category,
                               product_id=product_id,
                               item=item,
                               categories=categories)

    else:
        return render_template('productinfo.html',
                               category=category,
                               product_id=product_id,
                               item=item,
                               categories=categories)


# Delete Product
@app.route('/category/<int:category_id>/list/<int:product_id>/delete',
           methods=['GET', 'POST'])
def deleteProduct(category_id, product_id):
    """Delete a product in one specific category."""
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    #    itemToDelete = session.query(Product).filter_by(id=product_id).one()
    if login_session['user_id'] != category.user_id:
        flash('You are not permitted to delete this product. '
              'Please create your own product to delete.')
        return redirect(url_for('showList', category_id=category_id,
                                categories=categories))
    itemToDelete = session.query(Product).filter_by(id=product_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Successfully Deleted')
        return redirect(url_for('showList',
                                category_id=category_id,
                                categories=categories))
    else:
        return render_template('deleteproduct.html',
                               item=itemToDelete,
                               categories=categories)


# Show About page
@app.route('/about/')
def showAbout():
    """Show information page."""
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('about.html', categories=categories)


# Disconnect based on provider
@csrf.exempt
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    #app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    csrf_secret_key = 'csrf_secrets'
    app.run(host='0.0.0.0', port=8000)

