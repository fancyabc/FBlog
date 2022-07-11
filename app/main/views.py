from flask import abort, redirect, render_template,flash, request, session,url_for, send_from_directory,current_app
from flask_login import login_required, current_user

from . import main
from ..models import Permission, User, Role, Post
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from .. import db, avatars
from ..decorators import admin_required

'''处理博客文章的首页路由'''
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)

@main.route('/user/<username>') 
def user(username):     
    user = User.query.filter_by(username=username).first()   
    if user is None:
        abort(404)
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user, posts=posts)

'''server the image'''
@main.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main.route('/change-avatar/', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        raw_filename = avatars.save_avatar(f)
        u = current_user._get_current_object()
        u.avatar_raw = raw_filename
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('main.crop'))
    return render_template('change-avatar-upload.html')


@main.route('/change-avatar/crop/', methods=['GET', 'POST'])
@login_required
def crop():
    if request.method == 'POST':
        x = request.form.get('x')
        y = request.form.get('y')
        w = request.form.get('w')
        h = request.form.get('h')
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        u = current_user._get_current_object()
        u.avatar_s = filenames[0]
        u.avatar_m = filenames[1]
        u.avatar_l = filenames[2]
        db.session.add(u)
        db.session.commit()
        flash('更改头像成功', 'success')
        return redirect(url_for('main.user', username=u.username))
    return render_template('change-avatar-crop.html')


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)     
    form = EditProfileAdminForm(user=user)     
    if form.validate_on_submit():         
        user.email = form.email.data         
        user.username = form.username.data         
        user.confirmed = form.confirmed.data         
        user.role = Role.query.get(form.role.data)         
        user.name = form.name.data         
        user.location = form.location.data         
        user.about_me = form.about_me.data         
        db.session.add(user)         
        db.session.commit()         
        flash('The profile has been updated.')         
        return redirect(url_for('.user', username=user.username))     
    form.email.data = user.email     
    form.username.data = user.username     
    form.confirmed.data = user.confirmed     
    form.role.data = user.role_id     
    form.name.data = user.name     
    form.location.data = user.location     
    form.about_me.data = user.about_me     
    return render_template('edit_profile.html', form=form, user=user)

'''为文章提供固定链接'''
@main.route('/post/<int:id>') 
def post(id):     
    post = Post.query.get_or_404(id)     
    return render_template('post.html', posts=[post])

'''编辑博客文章的路由'''
@main.route('/edit/<int:id>', methods=['GET', 'POST']) 
@login_required 
def edit(id):     
    post = Post.query.get_or_404(id)     
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)     
    form = PostForm()     
    if form.validate_on_submit():         
        post.body = form.body.data         
        db.session.add(post)         
        db.session.commit()         
        flash('The post has been updated.')         
        return redirect(url_for('.post', id=post.id))     
    form.body.data = post.body     
    return render_template('edit_post.html', form=form)