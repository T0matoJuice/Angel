#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由模块 - 提供用户注册、登录、登出功能
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from modules.auth import db
from modules.auth.models import User
from modules.auth.captcha_utils import CaptchaGenerator, validate_captcha

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

# 创建验证码生成器实例
captcha_generator = CaptchaGenerator()


@auth_bp.route('/captcha')
def captcha():
    """生成验证码图片"""
    # 生成验证码
    code, image = captcha_generator.generate(length=4)

    # 将验证码存储在session中
    session['captcha_code'] = code

    # 返回图片
    return send_file(image, mimetype='image/png')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录

    GET: 显示登录页面
    POST: 处理登录请求
    """
    # 如果已登录，跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        captcha_input = request.form.get('captcha', '').strip()

        # 验证验证码
        stored_captcha = session.get('captcha_code', '')
        if not validate_captcha(captcha_input, stored_captcha):
            flash('验证码错误，请重新输入', 'error')
            # 清除旧的验证码
            session.pop('captcha_code', None)
            return render_template('auth/login.html')

        # 清除已使用的验证码
        session.pop('captcha_code', None)

        # 验证输入
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('auth/login.html')

        # 查询用户
        user = User.query.filter_by(username=username).first()

        if user is None:
            flash('用户名不存在', 'error')
            return render_template('auth/login.html')

        if not user.check_password(password):
            flash('密码错误', 'error')
            return render_template('auth/login.html')

        # 检查账户是否启用（is_active 字段为 varchar 类型，'1' 表示启用）
        if user.is_active != '1':
            flash('账户已被禁用，请联系管理员', 'error')
            return render_template('auth/login.html')

        # 登录成功
        login_user(user, remember=remember)
        flash(f'欢迎回来，{user.username}！', 'success')

        # 跳转到之前访问的页面或首页
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('common.index'))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册

    GET: 显示注册页面
    POST: 处理注册请求
    """
    # 如果已登录，跳转到首页
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        email = request.form.get('email', '').strip()
        captcha_input = request.form.get('captcha', '').strip()

        # 验证验证码
        stored_captcha = session.get('captcha_code', '')
        if not validate_captcha(captcha_input, stored_captcha):
            flash('验证码错误，请重新输入', 'error')
            # 清除旧的验证码
            session.pop('captcha_code', None)
            return render_template('auth/register.html')

        # 清除已使用的验证码
        session.pop('captcha_code', None)

        # 验证输入
        if not username:
            flash('请输入用户名', 'error')
            return render_template('auth/register.html')

        if len(username) < 3:
            flash('用户名至少需要3个字符', 'error')
            return render_template('auth/register.html')

        if not password:
            flash('请输入密码', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('密码至少需要6个字符', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('auth/register.html')

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在，请选择其他用户名', 'error')
            return render_template('auth/register.html')

        # 检查邮箱是否已存在（如果提供了邮箱）
        if email and User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('auth/register.html')

        # 创建新用户
        try:
            # 创建用户对象并设置字段
            user = User(
                username=username,
                email=email if email else None,
                role='user',  # 默认角色为普通用户
                creat_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 设置创建时间
                is_active='1'  # 默认启用账户（varchar 类型，'1' 表示启用）
            )
            user.set_password(password)  # 设置加密密码

            db.session.add(user)
            db.session.commit()

            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)}', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    username = current_user.username
    logout_user()
    flash(f'再见，{username}！', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人信息页面（可选功能）"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'creat_time': current_user.creat_time,
        'is_active': current_user.is_active
    })

