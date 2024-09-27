<script>
import { useAuthStore } from '@/stores/auth';
export default {
    name: 'NavBar',
    data(){
        return{
            showoptions: 'options'
        }
    },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        },
        hamburger_clicked(){
            if(this.showoptions == 'options'){
                this.showoptions = 'hideoptions'
            }
            else{
                this.showoptions = 'options'
            }
        },
    }
};
</script>

<template>
    <div class="navbar">
        <div class="left">
            <span class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></span>
            <button class="hamburger" @click="hamburger_clicked">&#9776;</button>
        </div>
        <ul :class="showoptions">
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
    </div>
</template>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}
.hamburger{
    display: none;
}

@media (max-width:768px) {
    .title {
        display: block;
    }
    .navbar {
        flex-direction: column;
        padding: 20px;
        padding-left: 0px;
        padding-right: 0px;
        width: 100%;
        margin: 0px;
        background-color: #f3f3f3;
    }
    .left{
        width:100%;
        display: flex;
        justify-content: space-between;
        padding:3px 3px 5px 3px;
    }
    .hideoptions li{
        display: none;
    }
    .options{
        background-color: #f3f3f3;
        display: block;
        flex-direction: column;
        margin: 0px;
        margin-top: 10px;
        width: 100%;
        border-bottom: black solid 2px;
    }
    .options li{
        max-width: 100%;
        padding:5px 3px 3px 3px;
        display: block;
        text-align: center;
        margin: 0px;
        border-width: 2px 0px 0px;
        border-style: solid;
        border-color: black;
    }
    .hamburger{
        display: inline;
        border: 2px solid;
        padding: 1px;
    }
}

</style>