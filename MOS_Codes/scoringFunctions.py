from config.config import yamlConfig
import os, importlib.util
from mos_logger import mos_logger as mos_log

class SingleScoringFunction:
    def __init__(self, _name, _path):
        self.name = _name
        self.path = _path

        module_name = os.path.splitext(os.path.basename(_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, _path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        function_to_call = getattr(module, _name)

        self.function = function_to_call
        self.weight = None
    

class ScoringFunctions:
    def __init__(self):
        self.scoringFunctions: list[SingleScoringFunction] = []

    def load_scoring_functions(self):
        # yamlFile has list of scoring functions, load them in a list of functions to execute
        try:
            for functionSpec in yamlConfig['MOS']['scoringFunctions']:
                function_name   = functionSpec['name']
                function_path   = functionSpec['path']

                self.scoringFunctions.append(SingleScoringFunction(function_name, function_path))

        except Exception as e:
            mos_log.error(f"Error loading scoring functions: {e}")
            raise e
    
    def setWeightForAllScoringFunction(self, _weightList):
        assert(len(_weightList) == len(self.scoringFunctions))
        for index, singleFunction in enumerate(self.scoringFunctions):
            singleFunction.weight = _weightList[index]

        self.normalize_weights()

    def normalize_weights(self):
        total_weight = 0.0
        for function in self.scoringFunctions:
            total_weight += function.weight

        for function in self.scoringFunctions:
            function.weight /= total_weight
        
allScoringFunctions = ScoringFunctions()
allScoringFunctions.load_scoring_functions()