
from omero.gateway import BlitzGateway, TagAnnotationWrapper
from omero_scoper.scopers import OmeroBaseScoper
class OmeroSlideScoper(OmeroBaseScoper):
    def __init__(self, conn: BlitzGateway, group_id: int = -1, exclusive_tagset_ids=[]):
        super().__init__(conn, group_id, exclusive_tagset_ids)
    
    def pull_info(self):
        """
        Pull the information about the slides from the OMERO server.
        """
        tagsets = self.organize_tagsets(self.conn.getObjects('TagAnnotation'))
        
        response = []
        for image_obj in self.conn.getObjects('Image'):
            image_props = {
                'name': image_obj.getName(),
                'id': image_obj.getId(),
                'roi_count': image_obj.getROICount(),
                'url': f'https://{self.hostname}/webclient/img_detail/{image_obj.getId()}',
            }

            # set default values for tags
            tag_map={}
            for tagset, children in tagsets.items():
                if tagset == 'orphan':
                    tag_map.update({tag.getTextValue(): 'False' for tag in children})
                    continue

                if tagset.getId() in self.exclusive_tagset_ids:
                    tag_map.update({tagset.getTextValue(): 'NA'})
                    continue
                tag_map.update({tag.getTextValue(): 'False' for tag in children})

            # add correct values to map
            for image_annot in image_obj.listAnnotations():
                if not isinstance(image_annot, TagAnnotationWrapper):
                    continue
                # if belongs to a nonexclusive tag, add normally
                image_annot_val = image_annot.getTextValue()
                if image_annot_val in tag_map.keys():
                    tag_map[image_annot_val] = 'true'
                    continue
                # should only be tags belonging to an exclusive tagset at this point
                for tagset, children in tagsets.items():
                    if image_annot.getId() in [x.getId() for x in children]:
                        tag_map[tagset.getTextValue()] = image_annot_val
                        break
            image_props.update(tag_map)

            response.append(image_props)
        return response