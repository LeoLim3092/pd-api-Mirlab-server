from rest_framework.permissions import IsAuthenticated, BasePermission


class ViewPatientListPermssion(BasePermission):
    codename = 'view_patient_list'
    describe = 'Can view patient list'

    def has_permission(self, request, view):
        return request.user.has_perm("api." + ViewPatientListPermssion.codename)