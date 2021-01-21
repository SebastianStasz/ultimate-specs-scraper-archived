class CarsData:
    def __init__(self, project_name, lineup):
        self.project_name = project_name
        self.lineup = lineup


class ModelLine:
    def __init__(
        self,
        model_line_name,
        model_line_desc,
        model_line_image,
        from_year,
        num_of_generations,
        num_of_models,
        generations,
    ):
        self.model_line_name = model_line_name
        self.model_line_desc = model_line_desc
        self.model_line_image = model_line_image
        self.from_year = from_year
        self.num_of_generations = num_of_generations
        self.num_of_models = num_of_models
        self.generations = generations


class Generation:
    def __init__(
        self,
        generation_number,
        generation_image,
        production_period,
        num_of_models,
        models,
    ):
        self.generation_number = generation_number
        self.generation_image = generation_image
        self.production_period = production_period
        self.num_of_models = num_of_models
        self.models = models


class Model:
    def __init__(self, model_name, model_code, model_image, engine_types):
        self.model_name = model_name
        self.model_code = model_code
        self.model_image = model_image
        self.engine_types = engine_types


class EngineType:
    def __init__(self, engine_type, num_of_versions, versions):
        self.engine_type = engine_type
        self.num_of_versions = num_of_versions
        self.versions = versions


class Version:
    def __init__(
        self, version_name, version_code, version_production_period, technical
    ):
        self.version_name = version_name
        self.version_code = version_code
        self.version_production_period = version_production_period
        self.technical = technical


class Technical:
    def __init__(self, category, specification):
        self.category = category
        self.specification = specification
