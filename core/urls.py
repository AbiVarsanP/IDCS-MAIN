from django.urls import path
from .views import *

urlpatterns = [
    path("",dash,name='dash'),
    path("notifications/", notifications_view, name="notifications_view"),
    path("profile/", student_profile, name='student_profile'),
    path("od/",od,name='od'),
    path("od/upload_proof_od/<int:id>",upload_proof_od,name='proof_od'),
    path("leave/",leave,name='leave'),
    path("leave/upload_proof_od/<int:id>",upload_proof_leave,name='proof_leave'),
    path("gatepass/",gatepass,name='gatepass'),
    path("feedback",student_feedback,name='student_feedback'),
    path("feedbackform/<int:id>/<str:typ>",student_feedback_form,name='student_feedback_form'),
    path('bonafide/', bonafide_view, name='bonafide'),
]

# staff

urlpatterns += [
    path("ods/check",staff_od_view,name='staff_od_view'),
    path("ods/action/<int:id>",staff_action_od,name='staff_action_od'),
    path("leaves/check",staff_leave_view,name='staff_leave_view'),
    path("leaves/action/<int:id>",staff_action_leave,name='staff_action_leave'),
    path("gatepasss/check",staff_gatepass_view,name='staff_gatepass_view'),
    path("gatepass/action/<int:id>",staff_action_gatepass,name='staff_action_gatepass'),
    path("bonafide/action/<int:id>", staff_action_bonafide, name="staff_action_bonafide"),
    path("bonafides/", staff_bonafides, name="staff_bonafides"),
    path("staff/notifications/", staff_notifications_view, name="staff_notifications"),
]
# hod

urlpatterns += [
    path("hods/check",hod_od_view,name='hod_od_view'),
    path("hleaves/check",hod_leave_view,name='hod_leave_view'),
    path("hgatepass/check",hod_gatepass_view,name='hod_gatepass_view'),
    path("hfeed/",hod_feedback_view,name="hod_feedback_view"),
    path("hfeed/toogle/<int:id>",hod_feedback_toggle,name='hod_feedback_toggle'),
    path("hfeed/hod_spot_feedback",hod_spot_feedback,name='hod_spot_feedback'),
    path("hfeed/spottoogle/<int:id>",hod_spot_feedback_toggle,name='hod_spot_feedback_toggle'),
    path("hbonafide/", hod_bonafide_view, name="hod_bonafide_view"),
    
]

# auth
urlpatterns+=[
    path("login",login_user,name='login'),
    path("logout",logout_user,name='logout')
]



# API

# R & D

# Placement




