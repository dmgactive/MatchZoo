"""DSSM Preprocessor."""

from matchzoo import engine
from matchzoo import preprocessor
from matchzoo import datapack


class DSSMPreprocessor(engine.BasePreprocessor):
    """
    DSSM preprocessor helper.

    Example:
        >>> train_inputs = [
        ...     ("beijing", "Beijing is capital of China", 1),
        ...     ("beijing", "China is in east Asia", 0),
        ...     ("beijing", "Summer in Beijing is hot.", 1)
        ... ]
        >>> dssm_preprocessor = DSSMPreprocessor()
        >>> rv_train = dssm_preprocessor.fit_transform(train_inputs)
        >>> type(rv_train)
        <class 'matchzoo.datapack.DataPack'>
        >>> test_inputs = [("beijing", "I visted beijing yesterday.")]
        >>> rv_test = dssm_preprocessor.transform(test_inputs)
        >>> type(rv_test)
        <class 'matchzoo.datapack.DataPack'>

    """

    def __init__(self):
        """Initialization."""
        self.context = {}
        super().__init__()

    def _detach_labels(self, inputs):
        """Detach."""
        unzipped_inputs = list(zip(*inputs))
        if len(unzipped_inputs) == 3:
            return zip(
                unzipped_inputs[0],
                unzipped_inputs[1]), unzipped_inputs[2]
        else:
            return zip(
                unzipped_inputs[0],
                unzipped_inputs[1]), None

    def _prepare_stateless_units(self):
        """Prepare."""
        return [
            preprocessor.TokenizeUnit(),
            preprocessor.LowercaseUnit(),
            preprocessor.PuncRemovalUnit(),
            preprocessor.StopRemovalUnit(),
            preprocessor.NgramLetterUnit()
        ]

    def _build_vocab(self, inputs):
        """Build vocabulary before fit transform."""
        vocab = []
        units = self._prepare_stateless_units()
        for left, right, label in inputs:
            for unit in units:
                left = unit.transform(left)
                right = unit.transform(right)
            # Extend tri-letters into vocab.
            vocab.extend(left + right)
        return vocab

    def fit(self, inputs):
        """Fit parameters."""
        vocab = self._build_vocab(inputs)
        vocab_unit = preprocessor.VocabularyUnit()
        vocab_unit.fit(vocab)
        self.context['term_index'] = vocab_unit.state['term_index']
        self.context['dim_triletter'] = len(vocab_unit.state['term_index']) + 1
        return self

    def transform(self, inputs):
        """Transform."""
        output_left = []
        output_righ = []
        units = self._prepare_stateless_units()
        term_index = self.context.get('term_index', None)
        if not term_index:
            raise ValueError(
                "Before apply transofm function, please fit term_index first!")
        units.append(preprocessor.WordHashingUnit(term_index))
        inputs, labels = self._detach_labels(inputs)
        for left, righ in inputs:
            for unit in units:
                left = unit.transform(left)
                righ = unit.transform(righ)
            output_left.append(left)
            output_righ.append(righ)
        if labels:
            return datapack.DataPack(
                data={
                    'text_left': output_left,
                    'text_right': output_righ,
                    'labels': labels
                },
                context=self.context)
        else:
            return datapack.DataPack(
                data={
                    'text_left': output_left,
                    'text_right': output_righ
                },
                context=self.context)
