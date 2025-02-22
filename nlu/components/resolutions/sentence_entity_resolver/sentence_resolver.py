from sparknlp_jsl.annotator import SentenceEntityResolverModel,SentenceEntityResolverApproach

class SentenceResolver:
    @staticmethod
    def get_pretrained_model(name, language, bucket='clinical/models'):
        return SentenceEntityResolverModel.pretrained(name, language,bucket) \
            .setInputCols(['entities',"sentence_embeddings"]) \
            .setDistanceFunction("COSINE") \
            .setNeighbours(3) \
            .setOutputCol("sentence_resolution")

    @staticmethod
    def get_default_trainable_model():
        return SentenceEntityResolverApproach() \
            .setNeighbours(25) \
            .setThreshold(1000) \
            .setInputCols(['entities',"sentence_embeddings"]) \
            .setNormalizedCol("_y") \
            .setLabelCol("y") \
            .setOutputCol('sentence_resolution') \
            .setDistanceFunction("EUCLIDIAN") \
            .setCaseSensitive(False)


""":cvar
TODO

for sentence resolvers
SENTENCE EMBEDS must be generated from CHUNK2DOC!!!!!!!!!!!!!
chunk2doc = Chunk2Doc().setInputCols("entities@modifier").setOutputCol("chunk2doc")



"""