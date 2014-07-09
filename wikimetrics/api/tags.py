from wikimetrics.models.storage import TagStore


class TagService(object):
    def get_all_tags(self, session):
        """
        Gets all the tags by name within the TagStore database
        """
        tags = session.query(TagStore.name).order_by(TagStore.name).all()
        flatten_tags = [item for sublist in tags for item in sublist]
        return flatten_tags
