"""
routes/trang_routes.py — Page routes (HTML).

Serves Jinja2 templates for all user-facing pages.
"""

from flask import Blueprint, render_template, request, redirect, url_for

trang_bp = Blueprint("trang", __name__)


@trang_bp.route("/")
def trang_chu():
    """Home / search page."""
    return render_template("trang_chu.html")


@trang_bp.route("/phan-tich")
def ket_qua():
    """Analysis results page — requires ?ma=<ticker>."""
    ma_cp = request.args.get("ma", "").strip().upper()
    if not ma_cp:
        return redirect(url_for("trang.trang_chu"))
    return render_template("ket_qua.html", ma_cp=ma_cp)


@trang_bp.route("/so-sanh")
def so_sanh():
    """Stock comparison page — optional ?ma=VNM,FPT pre-fills tickers."""
    ma_list_str = request.args.get("ma", "")
    ma_list = [m.strip().upper() for m in ma_list_str.split(",") if m.strip()]
    # Limit to 5
    ma_list = ma_list[:5]
    return render_template("so_sanh.html", ma_list=ma_list)
