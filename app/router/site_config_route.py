from flask import Blueprint , jsonify , request
from app.config.supabase_client import supabase

site_config_route = Blueprint('site', __name__)

# site , (delete set state ?)
@site_config_route.route('/get_site', methods=['POST'])
def get_site():
    try:
        body = request.get_json()
        user_id = int(body['user_id'])
        print(user_id)
        res = (
            supabase.table("site")
            .select("*, crane(*, camera(*), bank(*))")
            .eq("user_id", user_id)
            .execute()
        )
 
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
        return jsonify({'msg': 'Add new site sucessfuly'}), 201
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
        return jsonify({'msg':'update site completed !!!','data':res.data}) , 200
    except Exception as e :
        print("Error 'update new site:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

# crane (delete problem)
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
    
        return jsonify({'msg':'get crane detail success' ,'craneData' : res.data[0] })
            
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
        response = supabase.table('crane').insert({'site_id': site_id, 'crane_name': crane_name,'path_opc': path_opc,'id_wcs': id_wcs,}).execute()
        return jsonify({'msg': 'Add new crane sucessfuly'}), 201
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
        
        return jsonify({'msg':'update crane successfully!!' , 'data':res.data}) , 200

        
    except Exception as e :
        print("Error 'Add new crane:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

# cannot delete now becasue FK issue
@site_config_route.route('/delete_crane/<int:crane_id>' , methods=['DELETE'])
def delete_crane(crane_id):
    try:
        res = (supabase
               .table('crane')
               .delete()
               .eq('crane_id',int(crane_id))
               .execute())
        
        return jsonify({'msg':'delete crane sucess!!','delete data':res.data}) , 200
    except Exception as e :
        print('error', e)
        return jsonify({'error msg':str(e)}) , 500

# Camera route
@site_config_route.route('/add_camera', methods=['POST'])
def add_camera():
    try:
        data = request.json
        print(data, '<== hello camera')
        crane_id = data.get('crane_id')
        camera_url = data.get('camera_url')
        if not data:
            return jsonify({'status': 0}), 404
        response = supabase.table('camera').insert({'crane_id': crane_id, 'camera_url': camera_url}).execute()
        return jsonify({'msg': 'Add new camera sucessfuly' , 'latestData':response.data}), 201
    except Exception as e:
        print("Error 'Add new camera:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
    
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

        return jsonify({'msg': 'update new camera sucessfuly' , 'data' : res.data}), 200
    except Exception as e :
        print('error', e)
        return jsonify({'error msg':e}) , 500

@site_config_route.route('/delete_camera/<int:camera_id>' , methods=['DELETE'])
def delete_camera(camera_id):
    try:
        res = (supabase.table('camera').delete().eq('camera_id',camera_id).execute())
        print('In Delete method')
        return jsonify({'msg':'delete camera sucess!!'}) , 200
    except Exception as e :
        print('error', e)
        return jsonify({'error msg':e}) , 500

@site_config_route.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    try:
        data = request.get_json()
        camera_id = data.get('camera_id')
        activated_status = data.get('active_status')
        print(data)
        
        # Query the crane table
        res = supabase.table('camera').update({'camera_activate': activated_status}).eq('camera_id', camera_id).execute()
        result = {
            "msg": "toggle camera completed",
            "data": res.data
        }
      
        return jsonify(result), 200
    except Exception as e:
        print("Error 'Get Crane Detail':", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
    
# Bank  
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
        return jsonify({'msg': 'Add new bank sucessfuly' , 'data': res.data}), 201
    except Exception as e:
        print("Error 'add new bank:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
    
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
        
        return jsonify({'msg':'update bank success' , 'data':res.data}) , 200
    except Exception as e : 
        print("Error 'update bank:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
    
@site_config_route.route('/delete_bank/<int:bank_id>',methods=['DELETE'])
def delete_bank(bank_id):
    try:
        res = (supabase
               .table('bank')
               .delete()
               .eq('bank_id',int(bank_id))
               .execute())

        return jsonify({'msg':'delete bank successfully' ,'data':res.data}) , 200 
    except Exception as e :
        print("Error 'delete bank:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500