package com.ai.companion;

import org.mybatis.spring.mapper.MapperFactoryBean;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.Ordered;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class AiCompanionApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiCompanionApplication.class, args);
    }

    @Component
    public static class MyBatisPlusBeanFactoryPostProcessor implements BeanFactoryPostProcessor, Ordered {
        
        @Override
        public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) throws BeansException {
            // Do nothing - just to ensure MyBatis Plus beans are processed correctly
        }

        @Override
        public int getOrder() {
            return Ordered.LOWEST_PRECEDENCE;
        }
    }
}
