import json

class Controller:
    def __init__(self):
        self.url_tag = 'https://www.instagram.com/explore/tags/%s/?__a=1'

    def get_medias_by_tag(self,account_id, request, tag):
        """ Get media ID set, by your hashtag """
        self.media_by_tag =[]
        if account_id:
            log_string = "Get media id by tag: %s" % (tag)
            print(log_string)
            url_tag = self.url_tag % (tag)
            try:
                r = request.get(url_tag)
                all_data = json.loads(r.text)
                self.media_by_tag = list(all_data['graphql']['hashtag']['edge_hashtag_to_media']['edges'])
            except Exception as ex:
                print("Except on get_media!",str(ex))

        return self.media_by_tag
