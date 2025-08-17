# Updaters

## Introduction

Available data from the Envoy depends on the actual model, firmware, and installed components. The pyenphase library internally implements _Updaters_ to obtain the data. Each updater is specialized for one or more members of {py:class}`pyenphase.EnvoyData` and its _Probe_ method is called by {py:meth}`pyenphase.Envoy.probe` to detect whether the Envoy offers a specific dataset. If so, the probe method will return what data features it supports. If any are returned, the updaters _Update_ method is then used by {py:meth}`pyenphase.Envoy.update` to collect the actual data.

The various datasets relate to one or more {py:class}`pyenphase.const.SupportedFeatures` feature flags. For example, the
{py:data}`pyenphase.const.SupportedFeatures.PRODUCTION` supported feature flag relates to the
{py:class}`pyenphase.models.system_production.EnvoySystemProduction` data class which reports Solar production values. This flag can be set by either {py:class}`pyenphase.updaters.production.EnvoyProductionUpdater` or {py:class}`pyenphase.updaters.api_v1_production.EnvoyApiV1ProductionUpdater` updaters.

Multiple updaters may exist to provide data for a single dataset/feature. For example, Solar production data which is provided by all models may come from different sources. In the most basic Envoy model this data comes from a different endpoint compared to an Envoy equipped with Current Transformers. In both cases the updaters must be able to provide the same data for the {py:class}`pyenphase.models.system_production.EnvoySystemProduction` data class. This can be implemented in the same updater or in multiple updaters.

An updater is passed the previously identified features to its probe method. If its feature is already included in the passed list, the updater should back off and not report it again. As a result, only the first updater reporting the feature will be used for data collection.

An updater provides data for one or more features, typically (but not exclusively) sourced from a single endpoint on the Envoy. Multiple updaters may source from the same endpoint, as responses are locally cached during a single collection cycle to avoid duplicate requests.

Although each updater has its specific scope, some may need to share information with other updaters or make operational information available for common use in the {py:class}`pyenphase.Envoy` class. The probe methods can store this information in {py:class}`pyenphase.models.common.CommonProperties`. This information is reset by {py:meth}`CommonProperties.reset_probe_properties` at each probe start to avoid _sticking_ values.

The base class {py:class}`pyenphase.updaters.base.EnvoyUpdater` defines the abstract methods {py:meth}`pyenphase.updaters.base.EnvoyUpdater.probe` and {py:meth}`pyenphase.updaters.base.EnvoyUpdater.update`, which updaters must implement. Probe initializes the updater and is called during {py:meth}`pyenphase.Envoy.probe` (once per probe cycle); it must return a {py:class}`pyenphase.const.SupportedFeatures` mask indicating the data it can provide. Update is then invoked repeatedly to collect the data.
