import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import ErrorBoundary from '../ErrorBoundary.vue'

describe('ErrorBoundary', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } }
    ]
  })

  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div>Test Content</div>'
      },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('Test Content')
  })

  it('shows error message when hasError is true', async () => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div>Test Content</div>'
      },
      global: {
        plugins: [router]
      }
    })

    // Manually set error state
    wrapper.vm.hasError = true
    wrapper.vm.errorMessage = 'Test error message'
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Something went wrong')
    expect(wrapper.text()).toContain('Test error message')
  })

  it('has retry and go home buttons when error occurs', async () => {
    const wrapper = mount(ErrorBoundary, {
      slots: {
        default: '<div>Test Content</div>'
      },
      global: {
        plugins: [router]
      }
    })

    wrapper.vm.hasError = true
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThan(0)
    expect(wrapper.text()).toContain('Try Again')
    expect(wrapper.text()).toContain('Go to Home')
  })
})
