import inspect
import logging
logger = logging.getLogger('nlu')

from nlu.pipe.pipe_components import SparkNLUComponent
from nlu.pipe.component_utils import ComponentUtils
from nlu.pipe.storage_ref_utils import StorageRefUtils
# from nlu.pipe.pipeline import NLUPipeline
"""Pipe Level logic oprations and utils"""
class PipeUtils():
    @staticmethod
    def is_trainable_pipe(pipe):
        '''Check if pipe is trainable'''
        for c in pipe.components:
            if ComponentUtils.is_untrained_model(c):return True
        return False



    @staticmethod
    def enforece_AT_embedding_provider_output_col_name_schema_for_list_of_components  (pipe_list):
        """For every embedding provider, enforce that their output col is named <output_level>@storage_ref for output_levels word,chunk,sentence aka document , i.e. word_embed@elmo or sentence_embed@elmo etc.."""
        for c in pipe_list:
            if ComponentUtils.is_embedding_provider(c):
                level_AT_ref = ComponentUtils.extract_storage_ref_AT_notation(c, 'output')
                c.info.outputs = [level_AT_ref]
                c.info.spark_output_column_names = [level_AT_ref]
                c.model.setOutputCol(level_AT_ref[0])
                # if c.info.name =='ChunkEmbeddings' : c.model.setOutputCol(level_AT_ref[0])
                # else : c.model.setOutputCol(level_AT_ref)
        return pipe_list

    @staticmethod
    def enforce_AT_schema_on_embedding_processors  (pipe):
        """For every embedding provider and consumer, enforce that their output col is named <output_level>@storage_ref for output_levels word,chunk,sentence aka document , i.e. word_embed@elmo or sentence_embed@elmo etc.."""
        for c in pipe.components:
            if ComponentUtils.is_embedding_provider(c):
                if '@' not in c.info.outputs[0]:
                    level_AT_ref = ComponentUtils.extract_storage_ref_AT_notation(c, 'output')
                    c.info.outputs = [level_AT_ref]
                    c.info.spark_output_column_names = [level_AT_ref]
                    c.model.setOutputCol(level_AT_ref[0])

            if ComponentUtils.is_embedding_consumer(c):
                input_embed_col = ComponentUtils.extract_embed_col(c)
                if '@' not in input_embed_col:
                    storage_ref = StorageRefUtils.extract_storage_ref(c)
                    new_embed_col_with_AT_notation = input_embed_col+"@"+storage_ref
                    c.info.inputs.remove(input_embed_col)
                    c.info.inputs.append(new_embed_col_with_AT_notation)
                    c.info.spark_input_column_names.remove(input_embed_col)
                    c.info.spark_input_column_names.append(new_embed_col_with_AT_notation)
                    c.model.setInputCols(c.info.inputs)

                # if c.info.name =='ChunkEmbeddings' : c.model.setOutputCol(level_AT_ref[0])
                # else : c.model.setOutputCol(level_AT_ref)
        return pipe


    @staticmethod
    def enforce_NLU_columns_to_NLP_columns  (pipe):
        """for every component, set its inputs and outputs to the ones configured on the NLU component."""
        for c in pipe.components:
            if c.info.name == 'document_assembler' : continue
            c.model.setOutputCol(c.info.outputs[0])
            c.model.setInputCols(c.info.inputs)
            c.info.spark_input_column_names = c.info.inputs
            c.info.spark_output_column_names = c.info.outputs

        return pipe
    @staticmethod
    def is_converter_component_resolution_reference(reference:str)-> bool:
        if 'chunk_emb' in reference : return True
        if 'chunk_emb' in reference : return True

    @staticmethod
    def configure_component_output_levels_to_sentence(pipe):
        '''
        Configure pipe compunoents to output level document
        :param pipe: pipe to be configured
        :return: configured pipe
        '''
        for c in pipe.components:
            if 'token' in c.info.spark_output_column_names: continue
            # if 'document' in c.component_info.inputs and 'sentence' not in c.component_info.inputs  :
            if 'document' in c.info.inputs and 'sentence' not in c.info.inputs and 'sentence' not in c.info.outputs:
                logger.info(f"Configuring C={c.info.name}  of Type={type(c.model)}")
                c.info.inputs.remove('document')
                c.info.inputs.append('sentence')
                # c.component_info.spark_input_column_names.remove('document')
                # c.component_info.spark_input_column_names.append('sentence')
                c.model.setInputCols(c.info.spark_input_column_names)

            if 'document' in c.info.spark_input_column_names and 'sentence' not in c.info.spark_input_column_names and 'sentence' not in c.info.spark_output_column_names:
                c.info.spark_input_column_names.remove('document')
                c.info.spark_input_column_names.append('sentence')
                if c.info.type == 'sentence_embeddings':
                    c.info.output_level = 'sentence'

        return pipe

    @staticmethod
    def configure_component_output_levels_to_document(pipe):
        '''
        Configure pipe compunoents to output level document
        :param pipe: pipe to be configured
        :return: configured pipe
        '''
        logger.info('Configuring components to document level')
        # Every sentenceEmbedding can work on Dcument col
        # This works on the assuption that EVERY annotator that works on sentence col, can also work on document col. Douple Tripple verify later
        # here we could change the col name to doc_embedding potentially
        # 1. Configure every Annotator/Classifier that works on sentences to take in Document instead of sentence
        #  Note: This takes care of changing Sentence_embeddings to Document embeddings, since embedder runs on doc then.
        for c in pipe.components:
            if 'token' in c.info.spark_output_column_names: continue
            if 'sentence' in c.info.inputs and 'document' not in c.info.inputs:
                logger.info(f"Configuring C={c.info.name}  of Type={type(c.model)} input to document level")
                c.info.inputs.remove('sentence')
                c.info.inputs.append('document')

            if 'sentence' in c.info.spark_input_column_names and 'document' not in c.info.spark_input_column_names:
                # if 'sentence' in c.component_info.spark_input_column_names : c.component_info.spark_input_column_names.remove('sentence')
                c.info.spark_input_column_names.remove('sentence')
                c.info.spark_input_column_names.append('document')
                c.model.setInputCols(c.info.spark_input_column_names)

            if c.info.type == 'sentence_embeddings':  # convert sentence embeds to doc
                c.info.output_level = 'document'

        return pipe

    @staticmethod
    def configure_component_output_levels(pipe):
        '''
        This method configures sentenceEmbeddings and Classifier components to output at a specific level
        This method is called the first time .predit() is called and every time the output_level changed
        If output_level == Document, then sentence embeddings will be fed on Document col and classifiers recieve doc_embeds/doc_raw column, depending on if the classifier works with or withouth embeddings
        If output_level == sentence, then sentence embeddings will be fed on sentence col and classifiers recieve sentence_embeds/sentence_raw column, depending on if the classifier works with or withouth embeddings. IF sentence detector is missing, one will be added.

        '''
        if pipe.output_level == 'sentence':
            return PipeUtils.configure_component_output_levels_to_sentence(pipe)
        elif pipe.output_level == 'document':
            return PipeUtils.configure_component_output_levels_to_document(pipe)

    @staticmethod
    def check_if_component_is_in_pipe(pipe, component_name_to_check, check_strong=True):
        """Check if a component with a given name is already in a pipe """
        for c in pipe.components :
            if   check_strong and component_name_to_check == c.info.name : return True
            elif not check_strong and component_name_to_check in c.info.name : return True
        return False