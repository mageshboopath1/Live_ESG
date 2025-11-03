import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/company/:id',
    name: 'company',
    component: () => import('@/views/CompanyView.vue')
  },
  {
    path: '/comparison',
    name: 'comparison',
    component: () => import('@/views/ComparisonView.vue')
  },
  {
    path: '/scores/:companyId/:year',
    name: 'scores',
    component: () => import('@/views/ScoreView.vue')
  },
  {
    path: '/error',
    name: 'error',
    component: () => import('@/views/ErrorView.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Global error handler
router.onError((error) => {
  console.error('Router error:', error)
  router.push({
    name: 'error',
    query: { message: error.message }
  })
})

export default router
