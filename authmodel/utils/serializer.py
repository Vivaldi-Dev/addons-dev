class DlinkSerializer(object):

    def __init__(self, data=None, *args, **kwargs):
        self.data = data
        self.many = kwargs.get('many', False)
        self.meta = getattr(self, 'Meta', None)

        if not self.meta:
            raise ValueError("class Meta required")
        self.bytes = self.meta.__dict__.get('bytes', [])
        if not self.meta.__dict__.get('model', None):
            raise ValueError("model required on  Meta ")
        if not self.meta.__dict__.get('fields', None):
            raise ValueError("fields required on  Meta , can use __all__ or ['fielname']")

    def serializer(self):

        many = getattr(self, 'many', None)
        self.meta = getattr(self, 'Meta', None)
        if not self.data:
            if many:
                return []
            return None

        data_name = type(self.data).__dict__.get('_name', None)
        model_name = self.meta.model.__dict__.get('_name', None)
        if data_name != model_name or (data_name is None or model_name is None):
            raise ValueError("Query no support for this serializer")

        nif = self.meta.__dict__.get('nif', [])
        exclude = self.meta.__dict__.get('exclude', [])
        if not self.data:
            return None

        value_dict = {}
        value_array = []
        fields = self.meta.fields

        if many:
            objects_to_iterate = self.data
            if fields == '__all__':
                fields = self.data[0]._fields
        else:
            objects_to_iterate = [self.data]
            if fields == '__all__':
                fields = self.data._fields

        for obj in objects_to_iterate:
            value_dict = {}
            for f in fields:
                if f not in exclude:

                    className = type(getattr(obj, f)).__dict__.get('_name', None)

                    sclass = getattr(self, f, None)

                    if sclass:
                        if not className:
                            raise ValueError("This field can't serialize")
                        sclass.data = getattr(obj, f)
                        sclass.many = getattr(sclass, 'many', False)
                        sclass.bytes = getattr(sclass, 'bytes', [])
                        value_dict[f] = sclass.serializer()
                    else:

                        if className:
                            # print(f, str(type(obj._fields.get(f, None))))
                            if str(type(obj._fields.get(f, None))) == "<class 'odoo.fields.Many2one'>":

                                if len(getattr(obj, f)) > 0:
                                    value_dict[f] = getattr(obj, f).id
                                else:
                                    value_dict[f] = None
                            else:
                                value_dict[f] = [obj.id for obj in getattr(obj, f)]
                        else:
                            typeName = str(type(getattr(obj, f))).split("<class '")[1].split("'>")[0]

                            if not getattr(obj, f):
                                value_dict[f] = getattr(obj, f)
                                if f in nif and value_dict[f] == False:
                                    value_dict[f] = None
                            else:
                                if typeName == 'bytes':
                                    value_dict[f] = getattr(obj, f).decode('utf-8')
                                elif typeName == 'datetime.date':
                                    value_dict[f] = "{} {}".format(getattr(obj, f), "00:00:00")

                                elif typeName == 'datetime.datetime':
                                    value_dict[f] = "{}".format(getattr(obj, f))
                                else:
                                    value_dict[f] = getattr(obj, f)

            value_array.append(value_dict)

        if many:
            return value_array
        return value_dict
