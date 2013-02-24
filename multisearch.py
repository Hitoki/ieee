
def make_options(objects):
    from models import Node
    results = []
    for object in objects:
        if type(object) is Node:
            results.append({
                'name': object.name,
                'value': object.id,
            })
        else:
            results.append({
                'name': object.name,
                'value': object.id,
            })
    return results

def parse_input(object_type, id_list):
    # Passed a list of id's, convert them into objects first
    results = []
    if id_list != '':
        for id in id_list.split(','):
            results.append(object_type.objects.get(id=int(id)))
    return results
