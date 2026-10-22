from dataclasses import dataclass, asdict

@dataclass
class Product:
    name: str
    price: str
    description: str = None
    url: str = None
    image_url: str = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
