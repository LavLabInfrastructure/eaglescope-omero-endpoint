
from omero.gateway import BlitzGateway, TagAnnotationWrapper
from omero_scoper.scopers import OmeroBaseScoper

class OmeroSubjectScoper(OmeroBaseScoper):
    def __init__(self, conn: BlitzGateway, group_id: int = -1, exclusive_tagset_ids=[]):
        super().__init__(conn, group_id, exclusive_tagset_ids)
            
            
    def pull_info(self):
        """
        Pull the information about the slides from the OMERO server.
        """
        tagsets = self.organize_tagsets(self.conn.getObjects('TagAnnotation'))
        response = []
        for subject_obj in self.conn.getObjects('dataset'):
            children_count = 0
            roi_count = 0

            # set default values for tags
            tag_map={}
            for tagset, children in tagsets.items():
                if tagset == 'orphan':
                    tag_map.update({tag.getTextValue(): False for tag in children})
                    continue

                if tagset.getId() in self.exclusive_tagset_ids:
                    tag_map.update({tagset.getTextValue(): 'NA'})
                    continue
                tag_map.update({tag.getTextValue(): False for tag in children})

            # add correct values to map
            for subject_annot in subject_obj.listAnnotations():
                if not isinstance(subject_annot, TagAnnotationWrapper):
                    continue
                # if belongs to a nonexclusive tag, add normally
                subject_annot_val = subject_annot.getTextValue()
                if subject_annot_val in tag_map.keys():
                    tag_map[subject_annot_val] = True
                    continue
                # should only be tags belonging to an exclusive tagset at this point
                for tagset, children in tagsets.items():
                    if tagset == 'orphan':
                        continue
                    if subject_annot.getId() in [x.getId() for x in children]:
                        tag_map[tagset.getTextValue()] = subject_annot_val
                        break

            for image_obj in subject_obj.listChildren():
                # for each available tag, check if the image has the tag, making sure to only update false values with true
                for image_annot in image_obj.listAnnotations():
                    if not isinstance(image_annot, TagAnnotationWrapper):
                        continue
                    # if belongs to a nonexclusive tag, add normally
                    image_annot_val = image_annot.getTextValue()
                    if image_annot_val in tag_map.keys():
                        tag_map[image_annot_val] = True
                        continue
                    # should only be tags belonging to an exclusive tagset at this point
                    for tagset, children in tagsets.items():
                        if tagset == 'orphan':
                            continue
                        if image_annot.getId() in [x.getId() for x in children]:
                            tag_map[tagset.getTextValue()] = image_annot_val
                            break

                roi_count += image_obj.getROICount()
                children_count += 1

            subject_props = {
                'name': subject_obj.getName(),
                'id': subject_obj.getId(),
                'roi_count': roi_count,
                'slide_count': children_count,
                'url': f'https://{self.hostname}/webclient/?show=dataset-{subject_obj.getId()}',
            }
            subject_props.update(tag_map)

            response.append(subject_props)
        return response