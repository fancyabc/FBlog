from flask import (abort, redirect, render_template,flash, request, 
session,url_for, send_from_directory,current_app, make_response)
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries

from . import main
from ..models import Permission, User, Role, Post, Comment
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db, avatars
from ..decorators import admin_required,permission_required

'''处理博客文章的首页路由'''
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))     
    if show_followed:         
        query = current_user.followed_posts     
    else:         
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FBLOG_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, 
                            show_followed=show_followed,pagination=pagination)

'''查询所有文章还是所关注用户的文章'''
@main.route('/all') 
@login_required 
def show_all():     
    resp = make_response(redirect(url_for('.index')))     
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)  # 30天     
    return resp  
    
@main.route('/followed') 
@login_required 
def show_followed():     
    resp = make_response(redirect(url_for('.index')))     
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)  # 30天     
    return resp


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

'''支持博客文章评论'''
@main.route('/post/<int:id>', methods=['GET', 'POST']) 
def post(id):     
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                            post=post,
                            author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published!')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['FBLOG_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FBLOG_COMMENTS_PER_PAGE'], 
        error_out=False)     
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                            comments=comments, pagination=pagination)

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


@main.route('/follow/<username>') 
@login_required 
@permission_required(Permission.FOLLOW) 
def follow(username):     
    user = User.query.filter_by(username=username).first()     
    if user is None:         
        flash('Invalid user.')         
        return redirect(url_for('.index'))     
    if current_user.is_following(user):         
        flash('You are already following this user.')         
        return redirect(url_for('.user', username=username))     
    current_user.follow(user)     
    db.session.commit()     
    flash('You are now following %s.' % username)     
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)

'''管理评论的路由'''
@main.route('/moderate') 
@login_required 
@permission_required(Permission.MODERATE) 
def moderate():     
    page = request.args.get('page', 1, type=int)     
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FBLOG_COMMENTS_PER_PAGE'],         
        error_out=False)     
    comments = pagination.items     
    return render_template('moderate.html', comments=comments,
                            pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>') 
@login_required 
@permission_required(Permission.MODERATE) 
def moderate_enable(id):     
    comment = Comment.query.get_or_404(id)     
    comment.disabled = False     
    db.session.add(comment)
    db.session.commit()     
    return redirect(url_for('.moderate',
        page=request.args.get('page', 1, type=int)))  
        
@main.route('/moderate/disable/<int:id>')
@login_required 
@permission_required(Permission.MODERATE) 
def moderate_disable(id):     
    comment = Comment.query.get_or_404(id)     
    comment.disabled = True     
    db.session.add(comment)
    db.session.commit()      
    return redirect(url_for('.moderate',
        page=request.args.get('page', 1, type=int)))

'''报告缓慢的数据库查询'''
@main.after_app_request 
def after_request(response):     
    for query in get_debug_queries():         
        if query.duration >= current_app.config['FBLOG_SLOW_DB_QUERY_TIME']:             
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % 
                (query.statement, query.parameters, query.duration,
                query.context))     
    return response