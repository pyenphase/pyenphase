# Updaters

## Introduction

Available data from the Envoy depends on actual make, firmware and installed components for it. The pyenphase library internally implements what is called _Updaters_ to obtain the data. Each updater is specialized for one or more members of {py:class}`pyenphase.EnvoyData` and is used to detect, a.k.a. [_probe_](#pyenphase.Envoy.probe), if the Envoy offers this specific data set. If so, the updater is then used during the [_update_](#pyenphase.Envoy.update) method to collect the actual data.

The various datasets relate to one or more {py:class}`pyenphase.const.SupportedFeatures` feature flags. E.g. the
{py:data}`pyenphase.const.SupportedFeatures.PRODUCTION` supportedFeature identifier relates to the
{py:class}`pyenphase.models.system_production.EnvoySystemProduction` data class which reports Solar production values. This flag can be set by either {py:class}`pyenphase.updaters.production.EnvoyProductionUpdater` or {py:class}`pyenphase.updaters.api_v1_production.EnvoyApiV1ProductionUpdater` updaters.

Multiple updaters may exist to provide data for a single dataset/feature. E.g. Solar production data, in the most basic Envoy model this data
comes from a different endpoint compared to an Envoy equipped with Current Transformers. Both must be able to provide the same data for the
{py:class}`pyenphase.models.system_production.EnvoySystemProduction` data class.

An updater is passed the prior identified features to its probe method. If its feature is already included in the passed list, the updater should back off and not report it also. As a result only the first updater reporting the feature will be used for data collection.

An updater provides data for one or more features, typically but not exclusively, limited by and sourced from a single endpoint on the Envoy.
Multiple updaters may source from same endpoint as these are locally cached during a single collection cycle, avoiding multiple requests.

The base class {py:class}`pyenphase.updaters.base.EnvoyUpdater` provides the skeleton for an updater with the abstract methods
{py:meth}`pyenphase.updaters.base.EnvoyUpdater.probe` and {py:meth}`pyenphase.updaters.base.EnvoyUpdater.update` which need to be implemented by an updater. The _probe_ method is used to initialize the updater and is only called once and must signal capability to provide the data by returning a {py:class}`pyenphase.const.SupportedFeatures` mask it can support. The _update_ method is called repeatedly to collect the data.
