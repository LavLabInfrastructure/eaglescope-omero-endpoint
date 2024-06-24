
from omero.gateway import BlitzGateway
from omero_scoper.scopers import OmeroBaseScoper
class OmeroSubjectScoper(OmeroBaseScoper):
    def __init__(self, conn: BlitzGateway, group_id: int = -1, exclusive_tagset_ids=[]):
        super().__init__(conn, group_id)
    
    def pull_info(self):
        """
        Pull the information about the slides from the OMERO server.
        """
        tags = list(self.conn.getObjects('TagAnnotation'))
        
        response = []
        for subject_obj in self.conn.getObjects('dataset'):
            children_count = 0
            roi_count = 0
            tag_map = {tag.getTextValue(): False for tag in tags}
            subject_annots = list(subject_obj.listAnnotations())
            tag_map.update({tag.getTextValue(): (tag in subject_annots) for tag in tags if tag_map[tag.getTextValue()] is False})
            for image_obj in subject_obj.listChildren():
                # for each available tag, check if the image has the tag, making sure to only update false values with true
                img_annots = list(image_obj.listAnnotations())
                tag_map.update({tag.getTextValue(): (tag in img_annots) for tag in tags if tag_map[tag.getTextValue()] is False})

                roi_count += len(img_annots)
                children_count += 1

            subject_props = {
                'name': subject_obj.getName(),
                'id': subject_obj.getId(),
                'url': f'https://{self.hostname}/webclient/?show=dataset-{subject_obj.getId()}',
                'roi_count': roi_count,
                'slide_count': children_count,
            }
            subject_props.update(tag_map)

            response.append(subject_props)
        return response