import pprint
from flask import Blueprint , jsonify , request
from app.config.supabase_client import supabase

site_config_route = Blueprint('site', __name__)

# site 
@site_config_route.route('/get_site', methods=['POST'])
def get_site():
    try:
        body = request.get_json()
        user_id = int(body['user_id'])
        print(user_id)
        res = (
            supabase.table('site')
            .select('*, crane(*, camera(*), bank(*))')
            .order('site_id', desc=False)
            .eq('user_id', user_id)
            .eq('delete_status', False)
            .eq('crane.delete_status', False)
            .execute()
        )

        # sort crane id 
        for site in res.data:
            site['crane'].sort(key=lambda crane:crane['crane_id'])

        return jsonify({'msg':'get data success ' , 'siteData':res.data}) , 200
    except Exception as e :
        print(e)
        return jsonify({'err msg': e}) , 500

@site_config_route.route('/add_site', methods=['POST'])
def add_site():
    try:
        data = request.json
        data_json = data.get('data')
        print(data)
        user_id = data_json['user_id']
        company_id = data_json['company_id']
        site_name = data_json['site_name']

        if not data:
            return jsonify({'status': 0}), 404
        response = supabase.table('site').insert({'user_id': user_id,'company_id': company_id,'site_name': site_name,}).execute()
        return jsonify({'msg': 'Add new site sucessfully!'}), 201
    except Exception as e:
        print("Error 'Add new site:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

@site_config_route.route('/update_site', methods=['POST'])
def update_site():
    try:
        body = request.get_json()
        site_name = body['site_name']
        site_id = body['site_id']
        
        res = supabase.table('site').update({'site_name':site_name}).eq('site_id',site_id).execute()
        return jsonify({'msg':'Update site successfully!','data':res.data}) , 200
    except Exception as e :
        print("Error 'update new site:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

@site_config_route.route('/delete_site' , methods=['POST'])
def delete_site():
    try:
        body = request.get_json()
        site_id = int(body['site_id'])
        delete_status = bool(body['delete_status'])

        res = (supabase
               .table('site')
               .update({
                   'delete_status':delete_status,
               })
               .eq('site_id',site_id)
               .execute())
        
        return jsonify({'msg':'Delete site successfully!','data':res.data}) , 200
    except Exception as e :
        print("Error 'update new site:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

# crane 
@site_config_route.route('/get_crane_detail' , methods=['POST'])
def get_crane_detail():
    try:
        body = request.get_json()
        crane_id = body['crane_id']

        res = (supabase
               .table('crane')
               .select('*,camera(*) ,bank(*)')
               .eq('crane_id' , int(crane_id))
               .execute())

        # sort camera and bank
        for crane in res.data:
            crane['camera'].sort(key=lambda camera:camera['camera_id'])

        for crane in res.data:
            crane['bank'].sort(key=lambda bank:bank['bank_id'])

        return jsonify({'msg':'Get crane detail successfully!' ,'craneData' : res.data[0] })
            
    except Exception as e : 
        print(e)
        return jsonify({'err msg':e})

@site_config_route.route('/add_crane', methods=['POST'])
def add_crane():
    try:
        data = request.json
        crane_name = data.get('crane_name')
        path_opc = data.get('path_opc')
        id_wcs = data.get('id_wcs')
        site_id = data.get('site_id')
        if not data:
            return jsonify({'status': 0}), 404
        res = supabase.table('crane').insert({'site_id': site_id, 'crane_name': crane_name,'path_opc': path_opc,'id_wcs': id_wcs,}).execute()
        return jsonify({'msg': 'Add new crane successfully!','data':res.data}), 201
    except Exception as e:
        print("Error 'Add new crane:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

@site_config_route.route('/update_crane' , methods=['POST'])
def update_crane():
    try:
        body = request.get_json()
        crane_id = int(body['crane_id']) 
        crane_name = body['crane_name']
        path_opc = body['path_opc']
        id_wcs = body['id_wcs']

        res = (supabase
               .table('crane')
               .update({
                   'crane_name':crane_name,
                   'path_opc':path_opc,
                   'id_wcs':id_wcs
                })
                .eq('crane_id',crane_id)
                .execute()
               )
        
        return jsonify({'msg':'Update crane successfully!' , 'data':res.data}) , 200

        
    except Exception as e :
        print("Error 'Add new crane:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
 
@site_config_route.route('/delete_crane' , methods=['POST'])
def delete_crane():
    try:
        body = request.get_json()
        crane_id = body['crane_id']
        delete_status = body['delete_status']
        res = (supabase
               .table('crane')
               .update({
                   'delete_status':bool(delete_status)
               })
               .eq('crane_id',int(crane_id))
               .execute())
        
        return jsonify({'msg':'Delete crane successfully!','data':res.data}) , 200
    except Exception as e :
        print('error', e)
        return jsonify({'error msg':str(e)}) , 500

# camera
@site_config_route.route('/add_camera', methods=['POST'])
def add_camera():
    try:
        data = request.json
        crane_id = data.get('crane_id')
        camera_url = data.get('camera_url')

        if not data: return jsonify({'status': 0}), 404

        res = (supabase
                    .table('camera')
                    .insert({
                        'crane_id': crane_id, 
                        'camera_url': camera_url})
                    .execute())
        
        return jsonify({'msg': 'Add new camera sucessfuly' , 'latestData':res.data}), 201
    except Exception as e:
        print("Error 'Add new camera:", str(e))
        return jsonify({"msg": "Server error , error detail: " +str(e)}), 500
    
@site_config_route.route('/update_camera', methods=['POST'])
def update_camera():
    try:
        body = request.get_json()
        camera_url = body['new_camera_url']
        camera_id = body['camera_id']
        print(body)
        print(camera_id)
        print(camera_url)
        res = (supabase
               .table('camera')
               .update({'camera_url' : camera_url})
               .eq('camera_id',camera_id)
               .execute())

        return jsonify({'msg': 'Update camera sucessfully!' , 'data' : res.data}), 200
    except Exception as e :
        print('error', str(e))
        return jsonify({'msg':str(e)}) , 500

@site_config_route.route('/delete_camera/<int:camera_id>' , methods=['DELETE'])
def delete_camera(camera_id):
    try:
        res = (supabase
               .table('camera')
               .delete()
               .eq('camera_id',camera_id)
               .execute())

        return jsonify({'msg':'Delete camera successfully!','data':res.data}) , 200
    except Exception as e :
        print('error', e)
        return jsonify({'msg':e}) , 500

@site_config_route.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    try:
        data = request.get_json()
        camera_id = data.get('camera_id')
        activated_status = data.get('active_status')
        print(data)
        
        res = (supabase
            .table('camera')
            .update({'camera_activate': activated_status})
            .eq('camera_id', camera_id)
            .execute())
  
      
        return jsonify({'msg':'Toggle camera successfully!','data':res.data}), 200
    except Exception as e:
        print("Error 'Get Crane Detail':", str(e))
        return jsonify({"msg": "Server error , Error detail: "+ str(e)}), 500
    
# bank  
@site_config_route.route('/add_bank', methods=['POST'])
def add_bank():
    try:
        data = request.json
        bank = data.get('bank')
        level = data.get('level')
        bay = data.get('bay')
        crane_id = data.get('crane_id')
        if not data:
            return jsonify({'status': 0}), 404
        res = (supabase
                    .table('bank')
                    .insert({
                        'crane_id': crane_id, 
                        'bank': bank, 
                        'bay': bay, 
                        'level': level, })
                    .execute())
        return jsonify({'msg': 'Add new bank sucessfully!' , 'data': res.data}), 201
    except Exception as e:
        print("Error 'add new bank:", str(e))
        return jsonify({"msg": "Server error, Error detail: "+ str(e)}), 500
    
@site_config_route.route('/update_bank',methods=['POST'])
def update_bank():
    try:
        data = request.get_json()
        bank_id = data['bank_id']
        bank = data['bank']
        level = data['level']
        bay = data['bay']

        res = (supabase
               .table('bank')
               .update({
                   'bank':bank,
                   'level':level,
                   'bay':bay
               })
               .eq('bank_id',bank_id)
               .execute()
               )
        
        return jsonify({'msg':'Update bank successfully!' , 'data':res.data}) , 200
    except Exception as e : 
        print("Error 'update bank:", str(e))
        return jsonify({"msg": "Server error, Error Detail: "+ str(e)}), 500
    
@site_config_route.route('/delete_bank/<int:bank_id>',methods=['DELETE'])
def delete_bank(bank_id):
    try:
        res = (supabase
               .table('bank')
               .delete()
               .eq('bank_id',int(bank_id))
               .execute())

        return jsonify({'msg':'Delete bank successfully!' ,'data':res.data}) , 200 
    except Exception as e :
        print("Error 'delete bank:", str(e))
        return jsonify({"msg": "Server error, Error detail: "+ str(e)}), 500