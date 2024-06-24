
from omero.gateway import BlitzGateway
from omero_scoper.scopers import OmeroBaseScoper
class OmeroSlideScoper(OmeroBaseScoper):
    def __init__(self, conn: BlitzGateway, group_id: int = -1, exclusive_tagset_ids=[]):
        super().__init__(conn, group_id)
    
    def pull_info(self):
        """
        Pull the information about the slides from the OMERO server.
        """
        tags = list(self.conn.getObjects('TagAnnotation'))
        
        response = []
        for image_obj in self.conn.getObjects('Image'):
            image_props = {
                'name': image_obj.getName(),
                'id': image_obj.getId(),
                'url': f'https://{self.hostname}/webclient/img_detail/{image_obj.getId()}',
                'roi_count': image_obj.getROICount(),
            }

            img_annots = list(image_obj.listAnnotations())
            image_props.update({tag.getTextValue(): (tag in img_annots) for tag in tags})

            response.append(image_props)
        return response