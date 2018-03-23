# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-01-31

@author: Robin
'''
from base.defs import apiEx as ex
from base.utils import dic2obj, obj2dic, gen_pager_array, splitstrip
from base.views import ApiView, asapi
from base.defs import ApiParam as P
unlogin = asapi(logined=False)  # 无需登录的API
logined = asapi(logined=True)  # 需要登录的API

COORDTYPE = P(type=str, name="坐标类型", default='wgs84', choices=[('bd09ll', '百度经纬度坐标'), ('gcj02', '国测局加密坐标'), ('bd09', '百度坐标'), ('wgs84', 'GPS原始坐标')])

class BaseApiView(ApiView):
    def verify_objuser(self, obj):
        if hasattr(obj, 'user_id'):
            uid = getattr(obj, 'user_id')
            if uid != self.get_meid():
                raise ex(u'访问受限')
        return True
    
    def verify_phone(self, phone):
        from base.utils import isphone
        if not isphone(phone):
            raise ex(u'手机格式不对')
    
    def getIds(self, ids):
        if type(ids) != list and ids:
            ids = [i.strip() for i in ids.split(',') if i.strip()]
        return ids or []

    # 经纬度相关

    DEFAULT_COORDTYPE = 'wgs84'
    
    def transCoordinateOne(self, latitude, longitude, fromtype=COORDTYPE, totype=COORDTYPE):
        from base import gpsutils
        longitude = float(longitude)
        latitude = float(latitude)
        r = None
        if fromtype == totype:
            r = [longitude, latitude]
        elif fromtype == 'wgs84' and totype == 'bd09ll':
            r = gpsutils.wgs84togcj02(longitude, latitude)
            r = gpsutils.gcj02tobd09(r[0], r[1])
        elif fromtype == 'wgs84' and totype == 'gcj02':
            r = gpsutils.wgs84togcj02(longitude, latitude)
        elif fromtype == 'gcj02' and totype == 'wgs84':
            r = gpsutils.gcj02towgs84(longitude, latitude)
        elif fromtype == 'bd09ll' and totype == 'wgs84':
            r = gpsutils.bd09togcj02(longitude, latitude)
            r = gpsutils.gcj02towgs84(r[0], r[1])
        else:
            raise ex(u'未支持的类型:%s->%s' % (fromtype, totype))
        return r
    
    @unlogin
    def transCoordinate(self, latitude, longitude, fromtype=COORDTYPE, totype=COORDTYPE):
        '''转换坐标系'''
        r = self.transCoordinateOne(latitude, longitude, fromtype, totype)
        return {
                'coordtype':totype,
                'longitude':r[0],
                'latitude':r[1],
            }
        
    @unlogin
    def transCoordinates(self, latitudes, longitudes, fromtype=COORDTYPE, totype=COORDTYPE):
        '''批量转换坐标系'''
        lats = splitstrip(latitudes, ',')
        lngs = splitstrip(longitudes, ',')
        if len(lats) != len(lngs):
            raise ex(u'长度不相等')
        cs = []
        for lat, lng in zip(lats, lng):
            r = self.transCoordinateOne(lat, lng, fromtype, totype)
            cs.append({
                'longitude':r[0],
                'latitude':r[1],
            })
        return {
                'coordtype':totype,
                'items':cs
            }
        
    def getAddressResByLatLng(self, latitude, longitude, coordtype):
        import requests, json
#         latitude = float(latitude)
#         longitude = float(longitude)
        longitude,latitude = self.transCoordinateOne(latitude, longitude, coordtype, 'bd09ll')
        url = 'http://api.map.baidu.com/geocoder/v2/?ak=SielmFgNqoiIWlqrInY0BdAW&location=%s,%s&output=json&pois=0&coordtype=%s' % (latitude, longitude, coordtype)
        r = requests.request('get', url=url)
        res = json.loads(r.content)
        return res
    
    @unlogin
    def getAddressByLatLng(self, latitude, longitude, coordtype):
        res = self.getAddressResByLatLng(latitude, longitude, coordtype)
        try:
            from preset.models import Area
            adcode = res['result']['addressComponent']['adcode']
            data = res['result']['addressComponent']
            areanames = filter(lambda x: x, [data['province'], data['city'], data['district']])
            area = adcode and Area.objects.filter(code=adcode).first() or Area.getAreaByNames(u' '.join(areanames)) or None
            return {
                'coordtype':coordtype,
                'latitude':latitude,
                'longitude':longitude,
                'areanames':area and area.names,
                'address':res['result']['sematic_description'],
            }
        except Exception, e:
            print e
            raise ex(e.message)
    
    @unlogin
    def getLocationAddressText(self, latitude, longitude, coordtype=COORDTYPE):
        '''从经纬度获取地址信息'''
        res = self.getAddressResByLatLng(latitude, longitude, coordtype)
        r = {
                'coordtype':coordtype,
                'latitude':latitude,
                'longitude':longitude,
                'address':res['result']['formatted_address'] + res['result']['sematic_description']
            }
        return r

    @unlogin
    def getLocationAddress(self, latitude, longitude, coordtype=COORDTYPE):
        '''从经纬度获取地址, 参数:latitude, longitude'''
        return self.getAddressByLatLng(latitude, longitude, coordtype)
    
    @unlogin
    def getAreaByNames(self, names=P('名称', examples='云南省,昆明市,盘龙区',remark='使用逗号隔开')):
        '''根据名称获取区域'''
        from preset.models import Area
        names = splitstrip(names, ',')
        parea = None
        for name in names:
            area = Area.objects.filter(name=name).first() if not parea else Area.objects.filter(parent=parea, name=name).first()
            if not area:
                break
            parea = area
        return parea

    def getModel(self, modelname):
        model = self.get_model(modelname)
        if not model:
            raise ex(u'不存在模型:%s' % modelname)
        return model

    @unlogin
    def getQiniuToken(self):
        '''获取七牛上传凭证'''
        return {
                'token':self.site.qiniuuploadtoken
                }

    @unlogin
    def getUploadToken(self):
        '''获取上传凭证'''
        return {
                'token': self.site.qiniuuploadtoken if self.site.setting.get('qiniu_enable') else 'inner',
                'action': self.site.setting.get('irfile_upload_path') or (self.site.setting.get('qiniu_enable') and 'http://upload.qiniu.com/') or '/utils/upload.html'
                }
    

