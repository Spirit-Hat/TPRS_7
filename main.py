import tabulate
import numpy
import inspect
import sys


class ClassStats:
    def __init__(self):
        self.inheritance_depth = 0
        self.child_count = 0
        self.inherited_methods_count = 0
        self.overridden_methods_count = 0
        self.visible_methods_count = 0
        self.private_methods_count = 0

    def set_statistic(self, args: []):
        self.inherited_methods_count, self.overridden_methods_count, self.visible_methods_count, self.private_methods_count = args

    def get_statistic(self):
        return [self.inheritance_depth, self.child_count, self.inherited_methods_count, self.overridden_methods_count,
                self.visible_methods_count, self.private_methods_count]


class MetricCounter:
    def __init__(self):
        self.__cached_inheritance_depths: dict[type, int] = {}
        self.classes_stats: dict[type, ClassStats] = {}

    def count_class(self, example_class: type) -> ClassStats:
        class_metrics = ClassStats()
        class_metrics.child_count = len(example_class.__subclasses__())
        class_metrics.inheritance_depth = self.count_class_inheritance_depth(example_class)
        self.count_props(example_class, class_metrics)
        self.classes_stats[example_class] = class_metrics

    def count_class_inheritance_depth(self, example: type) -> int:
        if example in self.__cached_inheritance_depths:
            return self.__cached_inheritance_depths[example]
        if example.__base__ == object:
            inheritance_depth = 0
        else:
            inheritance_depth = self.count_class_inheritance_depth(example.__base__) + 1
        self.__cached_inheritance_depths[example] = inheritance_depth
        return inheritance_depth

    def count_props(self, example_class: type, out_stats: ClassStats):
        inherited_methods = 0
        overridden_methods = 0
        visible_methods = 0
        private_methods = 0
        for _name, member in inspect.getmembers(example_class):
            if inspect.isroutine(member):
                if _name not in example_class.__dict__:
                    inherited_methods += 1
                elif any(_name in super_class.__dict__ for super_class in example_class.mro()[1:]):
                    overridden_methods += 1
                if _name.startswith(f'_{example_class.__name__}') and not _name.endswith("__"):
                    private_methods += 1
                else:
                    visible_methods += 1

        out_stats.set_statistic([inherited_methods, overridden_methods, visible_methods, private_methods])

    def get_polymorphism_factor(self) -> float:
        total_overriden_count = 0
        total_child_count = 0
        for example_class, stats in self.classes_stats.items():
            total_overriden_count += stats.overridden_methods_count
            total_child_count += stats.child_count
        return 0 if total_overriden_count == 0 or total_child_count == 0 else total_overriden_count / total_child_count

    def get_method_inheritance_factor(self) -> float:
        inherited_methods = 0
        all_methods = 0
        for example_class, stats in self.classes_stats.items():
            inherited_methods += stats.overridden_methods_count
            all_methods += stats.inherited_methods_count + stats.overridden_methods_count
        return 0 if inherited_methods == 0 or all_methods == 0 else inherited_methods / all_methods

    def get_closed_methods_factor(self) -> float:
        private_methods = 0
        all_methods = 0
        for example_class, stats in self.classes_stats.items():
            private_methods += stats.private_methods_count
            all_methods += stats.visible_methods_count + stats.private_methods_count
        return 0 if private_methods == 0 or all_methods == 0 else private_methods / all_methods


def Init_MetricCounter(module: str) -> MetricCounter:
    model_class_list = MetricCounter()
    for _name, object in inspect.getmembers(sys.modules[module]):
        if inspect.isclass(object):
            model_class_list.count_class(object)
    return model_class_list


def class_stats_to_row(example_class: type, stats: ClassStats):
    _name = example_class.__name__
    values = stats.get_statistic()
    values.insert(0, _name)
    return [str(value) for value in values]


if __name__ == '__main__':
    package_counter = Init_MetricCounter('tabulate')
    table_headers = ["Name", "Inheritance Depth", "N-Children", "N-Inherited Methods", "N-Overridden Methods",
                     "N-Visible Methods", "N-Private Methods"]
    print(tabulate.tabulate(
        [class_stats_to_row(example_class, stats) for example_class, stats in package_counter.classes_stats.items()],
        headers=table_headers))

    lib_factors = {"Closed Methods Factor": [package_counter.get_closed_methods_factor()],
                   "Method Inheritance Factor": [package_counter.get_method_inheritance_factor()],
                   "Polymorphism Factor": [package_counter.get_polymorphism_factor()]}
    lib_factors_headers = ["Closed Methods Factor", "Method Inheritance Factor", "Polymorphism Factor"]
    print(tabulate.tabulate(lib_factors, headers="keys"))
