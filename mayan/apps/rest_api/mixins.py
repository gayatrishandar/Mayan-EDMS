from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ImproperlyConfigured

from rest_framework.settings import api_settings

from mayan.apps.acls.models import AccessControlList


class ExternalObjectListSerializerMixin(object):
    """
    Mixin to allow serializers to get a restricted object list with minimal code.
    This mixin adds the follow class Meta options to a serializer:
        external_object_list_model
        external_object_list_permission
        external_object_list_queryset
        external_object_list_pk_field
        external_object_list_pk_list_field

    The source queryset can also be provided overriding the
    .get_external_object_list() method.
    """
    def __init__(self, *args, **kwargs):
        super(ExternalObjectListSerializerMixin, self).__init__(*args, **kwargs)
        self.external_object_list_options = getattr(self, 'Meta', None)

    def get_external_object_list(self):
        queryset = self.get_external_object_list_queryset()

        if self.Meta.external_object_list_permission:
            queryset = AccessControlList.objects.restrict_queryset(
                permission=self.Meta.external_object_list_permission,
                queryset=queryset,
                user=self.context['request'].user
            )

        pk_field = self.get_external_object_list_option('pk_field')
        pk_list_field = self.get_external_object_list_option('pk_list_field')

        if not pk_field and not pk_list_field:
            raise ImproperlyConfigured(
                'ExternalObjectListSerializerMixin requires a '
                'external_object_list_pk_field a '
                'external_object_list_pk_list_field.'
            )

        if pk_field:
            pk_field_value = self.validated_data.get(pk_field)
        else:
            pk_field_value = None

        if pk_list_field:
            pk_list_field_value = self.validated_data.get(pk_list_field)
        else:
            pk_list_field = None

        if pk_field_value:
            id_list = (pk_field_value,)
        elif pk_list_field_value:
            id_list = (pk_list_field_value or '').split(',')
        else:
            id_list = ()

        return queryset.filter(pk__in=id_list)

    def get_external_object_list_option(self, option_name):
        return getattr(
            self.external_object_list_options, 'external_object_list_{}'.format(option_name),
            None
        )

    def get_external_object_list_queryset(self):
        model = self.get_external_object_list_option('model')
        queryset = self.get_external_object_list_option('queryset')

        if model:
            queryset = model._meta.default_manager.all()
        elif queryset:
            return queryset
        else:
            raise ImproperlyConfigured(
                'ExternalObjectListSerializerMixin requires a '
                'external_object_list_model or a external_object_list_queryset.'
            )

        return queryset


class SuccessHeadersMixin(object):
    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}
