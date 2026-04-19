{% extends "layout/base.html" %}
{% block title %}Tài khoản của tôi{% endblock %}

{% block content %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/account.css') }}">

<div class="acc-page">

  <!-- SIDEBAR -->
  <aside class="acc-sidebar">
    <div class="acc-avatar-wrap">
      <div class="acc-avatar" id="avatarCircle">
        {{ session.get('username', 'U')[0] | upper }}
      </div>
      <div class="acc-user-info">
        <p class="acc-name" id="displayName">{{ session.get('username', 'Người dùng') }}</p>
        <p class="acc-since">Thành viên</p>
      </div>
    </div>

    <nav class="acc-nav">
      <a href="#" class="acc-nav-item active" data-panel="profile">
        <i class="fa-solid fa-user"></i> Hồ sơ cá nhân
      </a>
      <a href="#" class="acc-nav-item" data-panel="security">
        <i class="fa-solid fa-lock"></i> Bảo mật
      </a>
      <a href="#" class="acc-nav-item" data-panel="history">
        <i class="fa-solid fa-clock-rotate-left"></i> Lịch sử đặt sân
      </a>
      <a href="#" class="acc-nav-item" data-panel="favorites">
        <i class="fa-solid fa-heart"></i> Sân yêu thích
      </a>
      <a href="{{ url_for('logout') }}" class="acc-nav-item acc-nav-logout">
        <i class="fa-solid fa-right-from-bracket"></i> Đăng xuất
      </a>
    </nav>
  </aside>

  <!-- MAIN CONTENT -->
  <main class="acc-main">

    <!-- ===== PANEL: HỒ SƠ ===== -->
    <div class="acc-panel active" id="panel-profile">
      <div class="acc-panel-header">
        <h2>Hồ sơ cá nhân</h2>
        <p>Quản lý thông tin tài khoản của bạn</p>
      </div>

      <div class="acc-card">
        <div class="acc-avatar-section">
          <div class="acc-avatar-lg" id="avatarLg">
            {{ session.get('username', 'U')[0] | upper }}
          </div>
          <div>
            <p class="acc-avatar-name">{{ session.get('username', '') }}</p>
            <p class="acc-avatar-sub">Tài khoản thường</p>
          </div>
        </div>

        <form id="profileForm" class="acc-form">
          <div class="acc-form-row">
            <div class="acc-form-group">
              <label>Tên đăng nhập</label>
              <input type="text" id="fUsername" placeholder="Tên đăng nhập"
                     value="{{ session.get('username', '') }}" readonly class="acc-input readonly">
            </div>
            <div class="acc-form-group">
              <label>Email</label>
              <input type="email" id="fEmail" placeholder="Email của bạn" class="acc-input">
            </div>
          </div>
          <div class="acc-form-row">
            <div class="acc-form-group">
              <label>Số điện thoại</label>
              <input type="text" id="fPhone" placeholder="0xxxxxxxxx" class="acc-input">
            </div>
            <div class="acc-form-group">
              <label>Loại tài khoản</label>
              <input type="text" value="Tài khoản thường" readonly class="acc-input readonly">
            </div>
          </div>
          <div class="acc-form-actions">
            <button type="button" class="acc-btn-save" onclick="saveProfile()">
              <i class="fa-solid fa-floppy-disk"></i> Lưu thay đổi
            </button>
          </div>
        </form>
      </div>

      <!-- Stats nhanh -->
      <div class="acc-stats-row">
        <div class="acc-stat-card">
          <i class="fa-solid fa-calendar-check acc-stat-icon blue"></i>
          <div>
            <p class="acc-stat-num" id="statBookings">--</p>
            <p class="acc-stat-label">Lần đặt sân</p>
          </div>
        </div>
        <div class="acc-stat-card">
          <i class="fa-solid fa-heart acc-stat-icon red"></i>
          <div>
            <p class="acc-stat-num" id="statFavs">--</p>
            <p class="acc-stat-label">Sân yêu thích</p>
          </div>
        </div>
        <div class="acc-stat-card">
          <i class="fa-solid fa-star acc-stat-icon yellow"></i>
          <div>
            <p class="acc-stat-num" id="statReviews">--</p>
            <p class="acc-stat-label">Đánh giá</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== PANEL: BẢO MẬT ===== -->
    <div class="acc-panel" id="panel-security">
      <div class="acc-panel-header">
        <h2>Bảo mật tài khoản</h2>
        <p>Cập nhật mật khẩu để bảo vệ tài khoản</p>
      </div>

      <div class="acc-card">
        <h3 class="acc-card-title"><i class="fa-solid fa-key"></i> Đổi mật khẩu</h3>
        <div class="acc-form">
          <div class="acc-form-group full">
            <label>Mật khẩu hiện tại</label>
            <div class="acc-input-pw">
              <input type="password" id="pwCurrent" placeholder="••••••••" class="acc-input">
              <span class="pw-toggle" onclick="togglePw('pwCurrent')"><i class="fa-solid fa-eye"></i></span>
            </div>
          </div>
          <div class="acc-form-row">
            <div class="acc-form-group">
              <label>Mật khẩu mới</label>
              <div class="acc-input-pw">
                <input type="password" id="pwNew" placeholder="••••••••" class="acc-input" oninput="checkPwStrength()">
                <span class="pw-toggle" onclick="togglePw('pwNew')"><i class="fa-solid fa-eye"></i></span>
              </div>
              <div class="pw-strength" id="pwStrength"></div>
            </div>
            <div class="acc-form-group">
              <label>Xác nhận mật khẩu mới</label>
              <div class="acc-input-pw">
                <input type="password" id="pwConfirm" placeholder="••••••••" class="acc-input">
                <span class="pw-toggle" onclick="togglePw('pwConfirm')"><i class="fa-solid fa-eye"></i></span>
              </div>
            </div>
          </div>

          <div class="pw-rules">
            <p class="pw-rule" id="rule-len"><i class="fa-solid fa-circle-xmark"></i> Ít nhất 8 ký tự</p>
            <p class="pw-rule" id="rule-upper"><i class="fa-solid fa-circle-xmark"></i> Có chữ hoa</p>
            <p class="pw-rule" id="rule-lower"><i class="fa-solid fa-circle-xmark"></i> Có chữ thường</p>
            <p class="pw-rule" id="rule-num"><i class="fa-solid fa-circle-xmark"></i> Có chữ số</p>
            <p class="pw-rule" id="rule-special"><i class="fa-solid fa-circle-xmark"></i> Có ký tự đặc biệt</p>
          </div>

          <div id="pwMsg" class="acc-msg"></div>

          <div class="acc-form-actions">
            <button type="button" class="acc-btn-save" onclick="changePassword()">
              <i class="fa-solid fa-shield-halved"></i> Cập nhật mật khẩu
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== PANEL: LỊCH SỬ ===== -->
    <div class="acc-panel" id="panel-history">
      <div class="acc-panel-header">
        <h2>Lịch sử đặt sân</h2>
        <p>Tất cả các lần bạn đã đặt sân</p>
      </div>
      <div id="historyList" class="acc-booking-list">
        <div class="acc-loading"><i class="fa-solid fa-spinner fa-spin"></i> Đang tải...</div>
      </div>
    </div>

    <!-- ===== PANEL: YÊU THÍCH ===== -->
    <div class="acc-panel" id="panel-favorites">
      <div class="acc-panel-header">
        <h2>Sân yêu thích</h2>
        <p>Những sân bạn đã lưu lại</p>
      </div>
      <div id="favList" class="acc-fav-grid">
        <div class="acc-loading"><i class="fa-solid fa-spinner fa-spin"></i> Đang tải...</div>
      </div>
    </div>

  </main>
</div>

<div id="accToast" class="acc-toast"></div>

<script src="{{ url_for('static', filename='js/account.js') }}"></script>
{% endblock %}