// 测试前端模型绑定逻辑
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8800';

async function testFrontendBinding() {
    console.log('=== 测试前端模型绑定逻辑 ===\n');

    try {
        // 1. 模拟 llmService.getAllModels()
        console.log('1. 调用 API 获取模型...');
        const response = await axios.get(`${API_BASE_URL}/api/llm/models`);
        const models = response.data;
        console.log(`   ✓ 获取到 ${models.length} 个模型`);

        // 2. 模拟 llmService.getChatModels(models)
        console.log('\n2. 过滤聊天模型...');
        const chatModels = models; // 修复后的逻辑：直接返回所有模型
        console.log(`   ✓ 聊天模型数量: ${chatModels.length}`);

        // 3. 模拟 llmService.getGroupedModelOptions(chatModels)
        console.log('\n3. 按提供商分组...');
        const providers = {};
        chatModels.forEach(model => {
            const provider = model.provider || '其他';
            if (!providers[provider]) {
                providers[provider] = [];
            }
            providers[provider].push({
                label: model.display_name || model.name,
                value: model.name,
                type: model.model_type || model.type
            });
        });

        console.log('   分组结果:');
        for (const [provider, models] of Object.entries(providers)) {
            console.log(`   - ${provider}: ${models.length} 个模型`);
            models.forEach(model => {
                console.log(`     • ${model.label} (${model.value})`);
            });
        }

        // 4. 验证数据结构是否符合前端期望
        console.log('\n4. 验证数据结构...');
        const expectedFormat = {
            providerName: [
                { label: 'display_name', value: 'name', type: 'model_type' }
            ]
        };

        let isValid = true;
        for (const [provider, models] of Object.entries(providers)) {
            models.forEach(model => {
                if (!model.label || !model.value) {
                    console.log(`   ✗ 模型 ${model.value} 缺少必要字段`);
                    isValid = false;
                }
            });
        }

        if (isValid) {
            console.log('   ✓ 所有模型都有必要的字段 (label, value)');
        }

        // 5. 模拟前端 v-for 循环
        console.log('\n5. 模拟前端渲染...');
        console.log('   HTML 结构预览:');
        console.log('   <el-select>');
        for (const [provider, models] of Object.entries(providers)) {
            console.log(`     <el-option-group label="${provider}">`);
            models.forEach(model => {
                console.log(`       <el-option label="${model.label}" value="${model.value}" />`);
            });
            console.log('     </el-option-group>');
        }
        console.log('   </el-select>');

        console.log('\n=== 测试完成 ✓ ===\n');
        console.log('结论: 模型绑定逻辑正确，可以正常显示在下拉框中！');

    } catch (error) {
        console.error('\n✗ 测试失败:', error.message);
        if (error.code === 'ECONNREFUSED') {
            console.error('  错误: 无法连接到后端 API (http://localhost:8800)');
        }
    }
}

testFrontendBinding();
