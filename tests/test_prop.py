from tests.testcase import DeviceTestCase


class TestPropPlugin(DeviceTestCase):
    async def test_get_props(self):
        props = await self.device.prop.properties
        self.assertGreater(len(props), 0)

        properties = await self.device.prop.properties
        prod_model = properties['ro.product.model']
        self.assertTrue(prod_model)
        
        prod_model = await self.device.prop.get('ro.product.model')
        self.assertTrue(prod_model)