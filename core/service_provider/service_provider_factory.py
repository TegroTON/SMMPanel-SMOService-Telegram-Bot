from .provider import ServiceProvider
from .smm_panel import SmmPanelProvider
from .smo_service import SmoServiceProvider


class ServiceProviderFactory:
    _providers = {
        SmmPanelProvider.name: SmmPanelProvider(),
        SmoServiceProvider.name: SmoServiceProvider(),
    }

    @staticmethod
    def get_provider(provider_name: str) -> ServiceProvider:
        provider = ServiceProviderFactory._providers[provider_name]
        return provider


service_provider_factory = ServiceProviderFactory()
